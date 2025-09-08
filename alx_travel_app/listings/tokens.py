import jwt, os
from datetime import datetime, timedelta

def expiration_time():
    expiry_time = datetime.now() + timedelta(minutes=5)
    return expiry_time

def get_token(user_id, email):
    payload = {
        "iss": str(user_id),
        "sub": email,
        "iat": int(datetime.now().timestamp()),
        "exp": int(expiration_time().timestamp())
    }

    with open('private.pem', 'rb') as file:
        key = file.read()
    token = jwt.encode(payload=payload, key=key, algorithm=os.environ.get("ALGORITHM"))
    return token

def decode_token(token):
    with open("public.pem", "rb") as file:
        key = file.read()
    
    try:
        payload = jwt.decode(token, key=key, algorithms=[os.environ.get("ALGORITHM")])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return False
    except jwt.InvalidSignatureError:
        print("Invalid signature")
        return False
    except jwt.InvalidIssuerError:
        print("Invalid issuer")
        return False
    except jwt.InvalidAudienceError:
        print("Invalid audience")
        return False
    except jwt.DecodeError:
        print("Malformed token")
        return False
    except jwt.InvalidTokenError:
        print("Invalid token")
        return False
