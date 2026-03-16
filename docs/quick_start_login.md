# Initial admin setup and security configration

1. Bootstrap (first startup)
Appliance/Assistant checks if any user exists in DB
If none → create UserInDB(username="admin", hashed_password=bcrypt(...random12+...), is_bootstrap=True, totp_secret=None)
Display random password once in UI/logs (never store plaintext)

2. Registration flow (after bootstrap login)
POST /auth/register with UserCreate
Generate TOTP secret (using pyotp.random_base32())
Generate totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(username, issuer_name="Network-Chan")
Return TOTPSetup → frontend shows QR
On verify (POST /auth/totp-verify with code) → save totp_secret to DB, set is_bootstrap=False on old admin → delete bootstrap record

3. Normal login
POST /auth/login with UserLogin
If user has totp_secret → require & verify totp_code via pyotp.TOTP(secret).verify(code, valid_window=1)
On success → issue JWT (fastapi-users / PyJWT / your own)
