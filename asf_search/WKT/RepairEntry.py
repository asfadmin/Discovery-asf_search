class RepairEntry:
    def __init__(self, report_type: str, report: str) -> None:
        self.report_type = report_type
        self.report = report
    
    def __str__(self) -> str:
        return f'{self.report_type}\n\t{self.report}'
