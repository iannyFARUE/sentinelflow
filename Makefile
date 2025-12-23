dev-seed:
	poetry run python -c "import httpx; httpx.post('http://127.0.0.1:8000/admin/seed').raise_for_status(); print('seeded')"

eval:
	EVAL_BASE_URL=http://127.0.0.1:8000 poetry run python eval/run_eval.py
