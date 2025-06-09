@echo off
echo Running migration to add user_id fields to content tables...
python migration_add_user_id.py
echo Migration completed.
pause 