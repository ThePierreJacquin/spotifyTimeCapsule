import pandas as pd
from datetime import datetime
import streamlit as st
import zipfile
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id="d5d44ede86f64d5e9f95aaf4198024a5",client_secret="e7d4d27fb03f4648a1d57461c8f11210"))
st.set_page_config(
    page_title="Spotify Bar Race Chart",
    page_icon="spotifyIcon.ico",
)

@st.cache_data()
def openZipFile()->pd.DataFrame:
    df = pd.DataFrame()
    with zipfile.ZipFile(st.session_state.file,"r") as z:
        for file in z.namelist():
            if file.startswith("MyData/endsong"):
                json = pd.read_json(z.open(file))
                df = pd.concat([df,json])
    df = df[~df["master_metadata_track_name"].isna()].reset_index()
    return df

@st.cache_data()
def process(df:pd.DataFrame)->pd.DataFrame:
    serie = df["ts"].apply(lambda x : str(x).split("T")[0][:7])
    timeSerie = serie.apply(lambda x: datetime(int(x.split("-")[0]),int(x.split("-")[1]),day=1))
    df["ts"]=timeSerie
    df = df[["ts","master_metadata_track_name","master_metadata_album_artist_name"]]
    df =df.rename(columns={"ts":"date",
                    "master_metadata_track_name":"songs",
                    "master_metadata_album_artist_name":"artists"})
    df = df.replace('\\$', '',regex=True)
    df = df.sort_values("date")
    return df

st.cache_data()
def TimeCapsule(df:pd.DataFrame,dateFrom,dateUntil):
    
    with st.spinner("Generating playlist ..."):
        playlist = []

    my_playlist = spotify.user_playlist_create(user="1144287826", name="Playlist "+str(dateFrom)+"--"+str(dateUntil), public=True,
                                      description="Time capsule from "+str(dateFrom)+" until " + str(dateUntil))
    return (my_playlist)
def loadSidebar(df:pd.DataFrame):
    with st.sidebar:
        st.markdown("<h1 style='text-align: center; font-size:2.5em;'> Statistics </h1>",unsafe_allow_html=True)
        st.markdown("---")
        left,right = st.columns([1,1])
        left.metric("Number of plays",len(df))
        right.metric("Period (days)",(df["date"].max()-df["date"].min()).days)

        left.metric("Differents artists",len(df["artists"].unique()))
        right.metric("Differents songs",len(df["songs"].unique()))

        st.markdown("---")
        left,right = st.columns([1,1])

        artist10 = df["artists"].value_counts()[:10].to_frame().rename(columns={"artists":"Plays"})
        left.title("Top artists")
        left.table(artist10)

        songs10 = df["songs"].value_counts()[:10].to_frame().rename(columns={0:"Plays"})
        right.title("Top songs")
        right.table(songs10)
    return None

st.title("Upload your 'My_Spotify_Data.zip'")
st.session_state.file = st.file_uploader("Upload your 'My_Spotify_Data.zip' file",type="zip",label_visibility="collapsed")

if st.session_state.file is None:
    st.warning("You want to upload your extended streaming history, not your account data")
    st.image("tutorial.png")
    st.info("To download those, you must first request them on your Spotify account, under the privacy tab.  It may takes up to a week to be available")
else:
    data = openZipFile()
    df = process(data)
    loadSidebar(df)
    with st.form("Settings"):
        timeframe_start,timeframe_end =  st.select_slider("What timeframe should I look at",df["date"],value=(df["date"].min(),df["date"].max()),format_func=lambda x: str(x)[:7].replace("-","/"))
        df = df[(df['date'] >= timeframe_start) & (df['date'] <= timeframe_end)]
        left,right = st.columns([1,1])
        if st.form_submit_button("Get Playlist"):
            st.session_state.playlist = TimeCapsule(df)
    if "palylist" in st.session_state:
        st.video(st.session_state.video)
        left,_,center,_,right = st.columns([1,1,1,1,1])
        center.download_button("Download",st.session_state.video,file_name="SpotifyBRC.m4v")