import os
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

def login(callback):
    auth_file = os.path.join(os.path.dirname(__file__), '..', 'auth.yaml')
    with open(auth_file) as file:
        config = yaml.load(file, Loader=SafeLoader)

    # Pre-hashing all plain text passwords once
    stauth.Hasher.hash_passwords(config['credentials'])

    try:
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
            auto_hash=False
        )

        authenticator.login()
    except Exception as e:
        st.error(e)

    if st.session_state.get('authentication_status'):
        # authenticator.logout()
        # st.write(f'Welcome *{st.session_state.get("name")}*')
        # st.title('Some content')
        callback()
    elif st.session_state.get('authentication_status') is False:
        st.error('Username/password is incorrect')
    elif st.session_state.get('authentication_status') is None:
        st.warning('Please enter your username and password')

    with open(auth_file, 'w') as file:
        yaml.dump(config, file, default_flow_style=False, allow_unicode=True)

