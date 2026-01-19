import time
import re
import streamlit as st
from streamlit_javascript import st_javascript


def get_device_coordinates(timeout=15):
    if st.session_state.get("coord_done", False):
        return (
            st.session_state.get("coord_lat"),
            st.session_state.get("coord_lng"),
        )

    if "coord_start_time" not in st.session_state or st.session_state.coord_start_time is None:
        st.session_state.coord_start_time = time.time()

    coords_json = st_javascript(
        "(function(){return new Promise(function(resolve){navigator.geolocation.getCurrentPosition(function(pos){resolve(JSON.stringify({latitude:pos.coords.latitude,longitude:pos.coords.longitude}));},function(){resolve(0);});});})()"
    )

    elapsed = time.time() - st.session_state.coord_start_time

    if isinstance(coords_json, str):
        lat_match = re.search(r'"latitude"\s*:\s*([-+]?\d*\.\d+|\d+)', coords_json)
        lon_match = re.search(r'"longitude"\s*:\s*([-+]?\d*\.\d+|\d+)', coords_json)

        if lat_match and lon_match:
            lat = float(lat_match.group(1))
            lng = float(lon_match.group(1))

            st.session_state.coord_lat = lat
            st.session_state.coord_lng = lng
            st.session_state.coord_done = True
            st.session_state.coord_start_time = None

            return lat, lng

    if elapsed > timeout:
        st.session_state.coord_done = True
        st.session_state.coord_lat = -1.0
        st.session_state.coord_lng = -1.0
        st.session_state.coord_start_time = None
        return -1.0, -1.0

    return None, None
