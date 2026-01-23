# GenshinChartPlayer

Allow you to play music in Genshin Impact.

## To-Do List

For users:

- [x] Basic chart parsing functionality
- [x] Note duration parsing
- [x] GUI for easier chart management and editing
- [x] Music playing (sound output)
- [x] Automatic ingame playing (simulated keyboard input)
- [x] Practice mode 

**Congratulations!** 🎉 We have finished the basic part of the project.

For advanced users / developers:

- [ ] configurable settings.
- [ ] customizable playing handlers
- [ ] ...and more! Feel free to issue or contribute!

## Installation

1. Ensure you have Python 3.11 or higher installed.
2. Clone this repository:
   ```bash
   git clone https://github.com/luckylaiCN/GenshinChartPlayer
    ```
3. Navigate to the project directory:
   ```bash
    cd GenshinChartPlayer
    ```
4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
## Usage
Run the main GUI application:
```bash
python main.py
```

## Important Information

### Audio Files

This project does not include any audio files. Users must provide their own audio files for the charts they wish to play. Ensure that you have the legal right to use any audio files you incorporate into your charts.

To add audio files to your charts, place them in the project directory `audio/` and name them with their key signatures (from `C3` to `B5`, sharps are not included). Files should be in `.mp3` format.

The default handler is located in [`player/handlers/sound_h.py`](https://github.com/luckylaiCN/GenshinChartPlayer/blob/main/player/handlers/sound_h.py).

### Packaging

When packaging the application for distribution using tools like PyInstaller, ensure that necessary assets should be included in the package. For example, you may need to include the `audio/` directory and any other resources your application depends on.

And worth to mention, this project is built upon `customtkinter` for GUI, therefore, you should not use `--onefile` option when packaging. Additionally, some extra steps may be required to ensure that `customtkinter` resources are correctly included in the packaged application. Please refer to [customtkinter's documentation](https://customtkinter.tomschimansky.com/documentation/packaging/) for more details.

Moreover, we dynamically load handlers from the `player/handlers/` directory. Make sure to include this directory and its contents in your package. Default handlers are `sound_h.py` and `keyboard_h.py`. Please make sure they are included to ensure the application functions correctly.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## DISCLAIMER

This project is not affiliated with or endorsed by miHoYo or HoYoverse. Use at your own risk.

This project does not provide any game assets or copyrighted materials. Users are responsible for ensuring they have the legal right to use any assets they incorporate into their charts. Users who use audio files or other assets that they do not own the rights to may be subject to legal action by the copyright holders.

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.