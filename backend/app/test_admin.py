import sys
sys.path.insert(0, '/app')
with open('/tmp/admin_test.txt', 'w') as f:
    try:
        from app.api.v1.endpoints import admin
        f.write('Import OK\n')
        f.write(f'Routes: {len(admin.router.routes)}\n')
        for r in admin.router.routes:
            f.write(f'  {r.methods} {r.path}\n')
    except Exception as e:
        f.write(f'ERROR: {e}\n')
        import traceback
        f.write(traceback.format_exc())
