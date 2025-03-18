python check_consistency.py --reset
python cli.py init
python cli.py index test_data
python check_consistency.py --fix
python test_db_consistency.py --all
