from app import app

# Vercel requires this handler
def handler(request, context):
    return app(request, context)

# This file is needed for Vercel deployment
if __name__ == '__main__':
    app.run()
