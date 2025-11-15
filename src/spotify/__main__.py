import asyncio
import sys
from spotify import spotify_get_data


def main():
    """Main function to get Spotify data and handle exceptions."""
    try:
        asyncio.run(spotify_get_data.main())
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
