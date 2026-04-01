"""
Stripe webhook handler — runs as a separate process alongside Streamlit.

Start with:
    uvicorn billing.webhook_server:app --port 8001

Then set your Stripe webhook endpoint to:
    https://yourdomain.com/webhook  (or use ngrok for local testing)
"""
try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("Run: pip install fastapi uvicorn")
    raise

from billing.stripe_client import handle_webhook

app = FastAPI(title="The Sharp — Webhook Server")


@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    result = handle_webhook(payload, sig_header)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return JSONResponse(content=result)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("billing.webhook_server:app", host="0.0.0.0", port=8001, reload=False)
