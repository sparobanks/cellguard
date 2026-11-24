.PHONY: help test data risk ckm suppress charts all clean

help:
	@echo "Targets:"
	@echo "  make test      run the unit tests"
	@echo "  make data      generate the synthetic microdata CSV"
	@echo "  make risk      assess disclosure risk (industry x region)"
	@echo "  make ckm       protect counts with the Cell Key Method"
	@echo "  make suppress  protect a magnitude table by cell suppression"
	@echo "  make charts    draw the risk-utility, spatial and ptable charts"
	@echo "  make all       run everything end to end"

test:
	python -m pytest -q

data:
	python scripts/generate_microdata.py

risk:
	python scripts/run_risk.py

ckm:
	python scripts/run_ckm.py

suppress:
	python scripts/run_suppress.py

charts:
	python scripts/make_ru_plot.py
	python scripts/make_spatial.py
	python scripts/make_ptable_plot.py

all: test data risk ckm suppress charts

clean:
	rm -rf reports/*.png reports/*.txt data/*.csv
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
