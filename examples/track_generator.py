from choralebricks.generators import tracks


def main():
    # iterate over all available tracks and get the path to the audio file
    for cur_track in list(tracks()):
        print(
            cur_track.path_audio.name,
            cur_track.voice,
            cur_track.instrument,
            cur_track.instrument_type
        )

if __name__ == "__main__":
    main()
