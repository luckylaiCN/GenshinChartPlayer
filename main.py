import argparse

from gui.app import run_app, AppProps

if __name__ == "__main__":
    parser = argparse.ArgumentParser("An app to empower your playing experience.")
    parser.add_argument("--admin", action="store_true", default=False)

    args = parser.parse_args()

    props: AppProps = {"admin": args.admin}
    run_app(props)
