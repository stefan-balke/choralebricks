from choralebricks.generators import tracks


def main():
    # iterate over all available tracks and get the path to the audio file
    for cur_track in tracks():
        print(cur_track.path_audio)

if __name__ == "__main__":
    main()
