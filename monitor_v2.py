#!/usr/bin/env python3
import time
import requests
import sys
from datetime import datetime

story_id = sys.argv[1] if len(sys.argv) > 1 else 'test-v2-1756417495'
url = f'http://localhost:5000/api/stories/{story_id}/status'

print(f'\nMonitoreando historia: {story_id}')
print('='*60)

start_time = time.time()
last_step = None

while True:
    try:
        response = requests.get(url)
        data = response.json()
        
        status = data.get('status', 'unknown')
        step = data.get('current_step', 'N/A')
        
        elapsed = int(time.time() - start_time)
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if step != last_step:
            print(f'[{timestamp}] [{elapsed:3d}s] {status:12} | {step}')
            last_step = step
        
        if status == 'completed':
            print(f'\n✅ Completado en {elapsed} segundos')
            result_url = f'http://localhost:5000/api/stories/{story_id}/result'
            result = requests.get(result_url).json()
            if 'titulo' in result:
                print(f'Título: {result["titulo"]}')
            break
            
        elif status == 'error':
            error = data.get('error', 'Unknown')
            print(f'\n❌ Error: {error[:150]}')
            break
            
        time.sleep(3)
        
    except KeyboardInterrupt:
        print('\n⏹️ Monitoreo cancelado')
        break
    except Exception as e:
        print(f'Error: {e}')
        break