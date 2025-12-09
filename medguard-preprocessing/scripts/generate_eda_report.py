from medguard.eda import PolarsEDAAnalyzer

analyser = PolarsEDAAnalyzer(data_path="patient-data-subset")

results = analyser.generate_eda_report(output_file="outputs/eda_report_001.html")
