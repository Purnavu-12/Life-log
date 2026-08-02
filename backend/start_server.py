#!/usr/bin/env python
import uvicorn
import os

os.environ['PORT'] = '8006'

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8006)