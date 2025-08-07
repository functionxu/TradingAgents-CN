import streamlit_authenticator as stauth

username = "dafenzi"
password = "688ad84c237ee"

hash_password = stauth.Hasher.hash_passwords(config['credentials'])

print(username)
print(password)
print(hash_password)
