import numpy as np

def compute_box_intersection_ratio(gear_box, person_box):
    """
    Computes the fraction of the gear box area that lies inside the person box.
    Returns ratio in range [0.0, 1.0].
    """
    gx1, gy1, gx2, gy2 = gear_box
    px1, py1, px2, py2 = person_box
    
    ix1 = max(gx1, px1)
    iy1 = max(gy1, py1)
    ix2 = min(gx2, px2)
    iy2 = min(gy2, py2)
    
    intersection_w = max(0.0, ix2 - ix1)
    intersection_h = max(0.0, iy2 - iy1)
    intersection_area = intersection_w * intersection_h
    
    gear_area = max(1.0, (gx2 - gx1) * (gy2 - gy1))
    return intersection_area / gear_area

def is_gear_associated_with_person(gear_item, person_box, min_overlap=0.25):
    """
    Checks if a detected gear item spatially belongs to a detected person.
    Utilizes vertical positional heuristics to ensure high accuracy.
    """
    gbox = gear_item['box']
    ratio = compute_box_intersection_ratio(gbox, person_box)
    
    if ratio < min_overlap:
        return False
        
    px1, py1, px2, py2 = person_box
    ph = max(1.0, py2 - py1)
    gx1, gy1, gx2, gy2 = gbox
    g_center_y = (gy1 + gy2) / 2.0
    
    # Relative vertical position (0.0 = top of person, 1.0 = bottom of person)
    rel_y = (g_center_y - py1) / ph
    gear_type = gear_item['class_name'].lower()
    
    if gear_type == 'helmet':
        return rel_y <= 0.55 or ratio > 0.4
    elif gear_type == 'vest':
        return 0.05 <= rel_y <= 0.90 or ratio > 0.4
    elif gear_type == 'glove':
        return 0.15 <= rel_y <= 0.95 or ratio > 0.3
    elif gear_type == 'boots':
        return rel_y >= 0.25 or ratio > 0.4
        
    return ratio >= min_overlap

def infer_workers_from_gear(gear_detections):
    """
    When explicit 'person' bounding boxes are absent, infers worker instances
    from spatial clustering of detected PPE gear items.
    """
    sorted_gear = sorted(gear_detections, key=lambda g: (g['box'][0] + g['box'][2]) / 2.0)
    workers = []
    
    for g in sorted_gear:
        gx1, gy1, gx2, gy2 = g['box']
        g_xc = (gx1 + gx2) / 2.0
        
        matched_w = None
        for w in workers:
            w_xc = (w['box'][0] + w['box'][2]) / 2.0
            w_width = max(80.0, w['box'][2] - w['box'][0])
            if abs(g_xc - w_xc) < w_width * 0.85:
                matched_w = w
                break
                
        if matched_w:
            matched_w['box'][0] = min(matched_w['box'][0], gx1)
            matched_w['box'][1] = min(matched_w['box'][1], gy1)
            matched_w['box'][2] = max(matched_w['box'][2], gx2)
            matched_w['box'][3] = max(matched_w['box'][3], gy2)
            matched_w['items'].append(g)
        else:
            gtype = g['class_name'].lower()
            if gtype == 'helmet':
                w_box = [gx1 - 25, gy1, gx2 + 25, gy1 + (gy2 - gy1) * 6.0]
            elif gtype == 'vest':
                w_box = [gx1 - 35, gy1 - (gy2 - gy1) * 0.5, gx2 + 35, gy2 + (gy2 - gy1) * 1.5]
            else:
                w_box = [gx1 - 25, gy1 - 50, gx2 + 25, gy2 + 50]
            workers.append({'box': w_box, 'confidence': g['confidence'], 'items': [g]})
            
    return [{'class_name': 'person', 'confidence': w['confidence'], 'box': w['box']} for w in workers]

def evaluate_compliance(detections, required_ppe=None, min_overlap=0.25):
    """
    Evaluates worker-wise compliance from detection objects.
    Accurately computes helmet, vest, glove, boot percentages, and safety index.
    """
    if required_ppe is None:
        required_ppe = ['helmet', 'vest', 'glove', 'boots']

    # Separate persons and gear detections
    person_detections = [d for d in detections if d['class_name'].lower() == 'person']
    gear_detections = [d for d in detections if d['class_name'].lower() in required_ppe]

    # If explicit person boxes are missing, infer worker instances from gear spatial clusters
    if not person_detections and gear_detections:
        person_detections = infer_workers_from_gear(gear_detections)

    workers = []
    
    for idx, p in enumerate(person_detections, 1):
        pbox = p['box']
        detected_gear = {item: False for item in required_ppe}
        gear_confidences = {item: 0.0 for item in required_ppe}
        
        # Associate gear items to this worker
        for g in gear_detections:
            gtype = g['class_name'].lower()
            if gtype in required_ppe and not detected_gear[gtype]:
                if is_gear_associated_with_person(g, pbox, min_overlap=min_overlap):
                    detected_gear[gtype] = True
                    gear_confidences[gtype] = g['confidence']
                    
        missing = [item for item, present in detected_gear.items() if not present]
        present_count = sum(1 for present in detected_gear.values() if present)
        total_required = len(required_ppe)
        score = (present_count / total_required * 100.0) if total_required > 0 else 100.0
        is_compliant = (len(missing) == 0)

        workers.append({
            'worker_id': idx,
            'box': pbox,
            'person_confidence': p['confidence'],
            'detected_items': detected_gear,
            'gear_confidences': gear_confidences,
            'missing_items': missing,
            'is_fully_compliant': is_compliant,
            'score': round(score, 1)
        })

    # Global summary statistics calculation
    total_workers = len(workers)
    compliant_workers = sum(1 for w in workers if w['is_fully_compliant'])
    
    if total_workers > 0:
        helmet_count = sum(1 for w in workers if w['detected_items'].get('helmet', False))
        vest_count = sum(1 for w in workers if w['detected_items'].get('vest', False))
        glove_count = sum(1 for w in workers if w['detected_items'].get('glove', False))
        boot_count = sum(1 for w in workers if w['detected_items'].get('boots', False))

        helmet_pct = round((helmet_count / total_workers) * 100.0, 1)
        vest_pct = round((vest_count / total_workers) * 100.0, 1)
        glove_pct = round((glove_count / total_workers) * 100.0, 1)
        boot_pct = round((boot_count / total_workers) * 100.0, 1)
        avg_score = round(sum(w['score'] for w in workers) / total_workers, 1)
    else:
        helmet_pct = 0.0
        vest_pct = 0.0
        glove_pct = 0.0
        boot_pct = 0.0
        avg_score = 0.0

    return {
        'total_workers': total_workers,
        'compliant_workers': compliant_workers,
        'non_compliant_workers': total_workers - compliant_workers,
        'helmet_compliance_pct': helmet_pct,
        'vest_compliance_pct': vest_pct,
        'glove_compliance_pct': glove_pct,
        'boot_compliance_pct': boot_pct,
        'overall_safety_score': avg_score,
        'workers': workers
    }
