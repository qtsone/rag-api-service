# services/api/app/postgresql_listener.py
import psycopg2
import psycopg2.extensions
import select
import json
import os
from typing import Callable, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgresListener:
    def __init__(self):
        self.conn: Optional[psycopg2.extensions.connection] = None
        self.callback: Optional[Callable] = None

    async def connect(self):
        """
        Establish connection to PostgreSQL
        """
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                host=os.getenv("POSTGRES_HOST")
            )
            self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("Successfully connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def setup_trigger(self):
        """
        Set up the trigger for note changes in HedgeDoc
        """
        if not self.conn:
            await self.connect()

        cur = self.conn.cursor()
        try:
            # Create trigger function
            cur.execute("""
                CREATE OR REPLACE FUNCTION notify_note_change()
                RETURNS trigger AS $$
                BEGIN
                    PERFORM pg_notify(
                        'note_changes',
                        json_build_object(
                            'operation', TG_OP,
                            'id', NEW.id,
                            'content', NEW.content,
                            'title', NEW.title,
                            'tags', NEW.tags,
                            'updateAt', NEW.updateAt
                        )::text
                    );
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)

            # Create trigger
            cur.execute("""
                DROP TRIGGER IF EXISTS notes_change_trigger ON "Notes";
                CREATE TRIGGER notes_change_trigger
                AFTER INSERT OR UPDATE ON "Notes"
                FOR EACH ROW
                EXECUTE FUNCTION notify_note_change();
            """)
            
            logger.info("Successfully set up PostgreSQL trigger")
        except Exception as e:
            logger.error(f"Failed to set up trigger: {e}")
            raise
        finally:
            cur.close()

    def register_callback(self, callback: Callable):
        """
        Register a callback function to handle notifications
        """
        self.callback = callback

    async def start_listening(self):
        """
        Start listening for notifications
        """
        if not self.conn:
            await self.connect()

        cur = self.conn.cursor()
        cur.execute("LISTEN note_changes;")
        logger.info("Started listening for PostgreSQL notifications")

        while True:
            if select.select([self.conn], [], [], 5) != ([], [], []):
                self.conn.poll()
                while self.conn.notifies:
                    notify = self.conn.notifies.pop(0)
                    if self.callback:
                        try:
                            payload = json.loads(notify.payload)
                            await self.callback(payload)
                        except Exception as e:
                            logger.error(f"Error processing notification: {e}")

    async def close(self):
        """
        Close the PostgreSQL connection
        """
        if self.conn:
            self.conn.close()
            logger.info("Closed PostgreSQL connection")
