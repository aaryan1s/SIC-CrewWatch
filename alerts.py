from datetime import datetime

def generate_alerts(compliance_result):
    """
    Generates structured safety alerts based on worker compliance evaluation.
    Categorizes alerts into CRITICAL, WARNING, and SUCCESS.
    """
    alerts = []
    timestamp = datetime.now().strftime("%H:%M:%S")
    workers = compliance_result.get('workers', [])

    for worker in workers:
        w_id = worker['worker_id']
        missing = worker['missing_items']
        
        if not missing:
            alerts.append({
                'worker_id': w_id,
                'severity': 'SUCCESS',
                'title': f"Worker #{w_id} - Fully Compliant",
                'message': f"Worker #{w_id} is wearing all required PPE (Helmet, Vest, Gloves, Boots).",
                'missing_items': [],
                'timestamp': timestamp
            })
        else:
            has_critical_missing = any(item in ['helmet', 'vest'] for item in missing)
            severity = 'CRITICAL' if has_critical_missing else 'WARNING'
            missing_str = ", ".join([m.capitalize() for m in missing])
            
            alerts.append({
                'worker_id': w_id,
                'severity': severity,
                'title': f"Worker #{w_id} - Safety Violation",
                'message': f"Missing mandatory PPE equipment: {missing_str}.",
                'missing_items': missing,
                'timestamp': timestamp
            })

    return alerts
