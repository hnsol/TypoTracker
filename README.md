# TypoTracker

TypoTracker is a Python script designed to track keyboard inputs and send notifications when specific key bindings are activated. This tool is intended to run in any environment where Python is available, making it suitable for various use cases including analyzing typing habits and monitoring keyboard activity.

## Features

- Keyboard input tracking.
- Customizable key bindings.
- Support for notification systems based on the operating system (currently only macOS).

## Setup

1. **Install Dependencies**:
   TypoTracker requires `pynput` and `yaml`. Install these packages using the following command:

   ```
   pip install pynput pyyaml
   ```

2. **Configure Settings**:
   Edit the `ttconfig.yaml` file to customize the following settings:

   - `log_file_path`: Path to the file where logs will be saved.
   - `debug_mode`: Enable or disable debug mode.
   - `trigger_key`: Key bindings to trigger TypoTracker.
   - `notification_type`: Type of notification system to use ('macOS', 'Windows', 'Linux', 'None').

   Example configuration:

   ```yaml
   log_file_path: "/path/to/logfile"
   debug_mode: False
   trigger_key:
     ctrl: True
     shift: True
     alt: False
     cmd: False
     key: 'l'
   notification_type: 'macOS'
   ```

## Usage

To run the script, use the following command:

```
python typotracker.py
```

## License

This project is released under the [MIT License](LICENSE).

