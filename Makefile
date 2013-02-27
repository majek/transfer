
all: venv/.ok
	# ./venv/bin/python -m transfer.main data3
	# python -m transfer.training_data data3 --window=16
	# python -m transfer.training_data data3


venv:
	virtualenv --system-site-packages venv
	-rm distribute-*.tar.gz || true

venv/.ok: venv Makefile requirements.txt
	./venv/bin/pip install -r requirements.txt
	touch venv/.ok
