"""
Toplu Barkod & 10x10cm Termal Kargo Etiket Sistemi - Flask Sunucusu
Port: 5005
"""

import os
import io
import json
import glob
import webbrowser
import threading
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from core_barcode import read_excel_or_csv, extract_items, generate_labels_pdf, create_sample_excel

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
IS_VERCEL = bool(os.environ.get('VERCEL'))
if IS_VERCEL:
    UPLOAD_FOLDER = '/tmp'
else:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SESSION_CACHE = {
    'headers': [],
    'data_rows': [],
    'mapping': {},
    'items': []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Lütfen bir dosya seçin.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Dosya seçilmedi.'}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.xlsx', '.xls', '.csv']:
        return jsonify({'success': False, 'message': 'Yalnızca .xlsx, .xls veya .csv dosyaları desteklenir.'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    try:
        headers, data_rows, mapping = read_excel_or_csv(file_path)
        if not headers or not data_rows:
            return jsonify({'success': False, 'message': 'Dosyada geçerli veri veya başlık satırı bulunamadı.'}), 400

        items = extract_items(headers, data_rows, mapping)
        
        SESSION_CACHE['headers'] = headers
        SESSION_CACHE['data_rows'] = data_rows
        SESSION_CACHE['mapping'] = mapping
        SESSION_CACHE['items'] = items

        total_labels = sum(item['quantity'] for item in items)

        return jsonify({
            'success': True,
            'filename': filename,
            'headers': headers,
            'mapping': mapping,
            'items': items,
            'total_items': len(items),
            'total_labels': total_labels
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Dosya işlenirken hata oluştu: {str(e)}'}), 500
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

@app.route('/api/remap', methods=['POST'])
def remap_columns():
    data = request.get_json() or {}
    headers = SESSION_CACHE.get('headers', [])
    data_rows = SESSION_CACHE.get('data_rows', [])

    if not headers or not data_rows:
        return jsonify({'success': False, 'message': 'Aktif dosya bulunamadı.'}), 400

    def parse_idx(key):
        val = data.get(key)
        return int(val) if val is not None and str(val).isdigit() else None

    mapping = {
        'cust_idx': parse_idx('cust_idx'),
        'addr_idx': parse_idx('addr_idx'),
        'dist_idx': parse_idx('dist_idx'),
        'city_idx': parse_idx('city_idx'),
        'phone_idx': parse_idx('phone_idx'),
        'barcode_idx': parse_idx('barcode_idx'),
        'name_idx': parse_idx('name_idx'),
        'qty_idx': parse_idx('qty_idx'),
    }

    items = extract_items(headers, data_rows, mapping)
    SESSION_CACHE['mapping'] = mapping
    SESSION_CACHE['items'] = items

    total_labels = sum(item['quantity'] for item in items)
    return jsonify({
        'success': True,
        'mapping': mapping,
        'items': items,
        'total_items': len(items),
        'total_labels': total_labels
    })

@app.route('/api/load-sample', methods=['GET'])
def load_sample_data():
    sample_bytes = create_sample_excel()
    sample_path = os.path.join(UPLOAD_FOLDER, 'sample_temp.xlsx')
    with open(sample_path, 'wb') as f:
        f.write(sample_bytes)

    headers, data_rows, mapping = read_excel_or_csv(sample_path)
    items = extract_items(headers, data_rows, mapping)
    
    SESSION_CACHE['headers'] = headers
    SESSION_CACHE['data_rows'] = data_rows
    SESSION_CACHE['mapping'] = mapping
    SESSION_CACHE['items'] = items

    if os.path.exists(sample_path):
        os.remove(sample_path)

    total_labels = sum(item['quantity'] for item in items)
    return jsonify({
        'success': True,
        'filename': 'Ornek_Kargo_Listesi.xlsx',
        'headers': headers,
        'mapping': mapping,
        'items': items,
        'total_items': len(items),
        'total_labels': total_labels
    })

@app.route('/api/download-sample-excel', methods=['GET'])
def download_sample_excel():
    buf_bytes = create_sample_excel()
    return send_file(
        io.BytesIO(buf_bytes),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='Ornek_Kargo_Listesi.xlsx'
    )

@app.route('/api/load-downloads', methods=['GET'])
def load_recent_downloads():
    downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    if not os.path.exists(downloads_path):
        return jsonify({'success': False, 'message': 'İndirilenler klasörü bulunamadı.'}), 404

    patterns = ['*.xlsx', '*.xls', '*.csv']
    candidates = []
    for pat in patterns:
        candidates.extend(glob.glob(os.path.join(downloads_path, pat)))

    candidates = [f for f in candidates if not os.path.basename(f).startswith('~$')]
    if not candidates:
        return jsonify({'success': False, 'message': 'İndirilenler klasöründe Excel dosyası bulunamadı.'}), 404

    latest_file = max(candidates, key=os.path.getmtime)
    filename = os.path.basename(latest_file)

    try:
        headers, data_rows, mapping = read_excel_or_csv(latest_file)
        if not headers or not data_rows:
            return jsonify({'success': False, 'message': f'{filename} dosyasında geçerli veri bulunamadı.'}), 400

        items = extract_items(headers, data_rows, mapping)
        SESSION_CACHE['headers'] = headers
        SESSION_CACHE['data_rows'] = data_rows
        SESSION_CACHE['mapping'] = mapping
        SESSION_CACHE['items'] = items

        total_labels = sum(item['quantity'] for item in items)
        return jsonify({
            'success': True,
            'filename': filename,
            'headers': headers,
            'mapping': mapping,
            'items': items,
            'total_items': len(items),
            'total_labels': total_labels
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Dosya okunurken hata: {str(e)}'}), 500

@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf_endpoint():
    data = request.get_json() or {}
    items = data.get('items', [])
    options = data.get('options', {})

    if not items:
        items = SESSION_CACHE.get('items', [])

    if not items:
        return jsonify({'success': False, 'message': 'PDF üretilecek sipariş listesi bulunamadı.'}), 400

    try:
        pdf_bytes = generate_labels_pdf(items, options)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='Kargo_Barkod_10x10cm.pdf'
        )
    except Exception as e:
        return jsonify({'success': False, 'message': f'PDF oluşturulamadı: {str(e)}'}), 500

def open_browser():
    try:
        webbrowser.open_new('http://127.0.0.1:5005')
    except Exception:
        pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5005))
    threading.Timer(1.0, open_browser).start()
    print(f"\n=======================================================")
    print(f"  TOPLU BARKOD & KARGO ETİKET SİSTEMİ BAŞLATILDI")
    print(f"  URL: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host='0.0.0.0', port=port, debug=False)
