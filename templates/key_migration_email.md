# Action Required: API Key Security Upgrade

Hello,

We've upgraded the security of our HarmonyØ4 API. Your current API key uses outdated encryption and needs to be replaced.

## 🔐 What You Need to Do

1. Create a new API key using our updated system:

curl -X POST https://api.yourdomain.com/api-keys \
  -H "X-API-Key: YOUR_CURRENT_KEY" \
  -H "Content-Type: application/json" \
  -d '{"label": "Secure Key"}'

2. Save the new key displayed in the response. It will not be shown again.
3. Update your applications to use the new key.
4. Your old key will stop working on {DEADLINE_DATE}.

## 📅 Timeline

- Now: Create new key immediately
- {WARNING_DATE}: Warning emails sent
- {DEADLINE_DATE}: Legacy keys disabled

## 🆘 Need Help?

Contact support@yourdomain.com or visit our migration guide:
https://docs.yourdomain.com/security-upgrade

Thank you for helping us keep your data secure!

Best regards,
The HarmonyØ4 Team
