# Productivity Game

Welcome to the **Productivity Game**, a fun and interactive way to boost your productivity while enjoying a gamified experience. This project combines a Pomodoro timer, task management, calendar, and a reward-based game to help you stay focused and motivated.

## Features

### 1. Pomodoro Timer
- **Focus Sessions**: Start focus sessions with customizable durations.
- **Breaks**: Short and long breaks to recharge.
- **Sound Alerts**: Optional sound notifications for session transitions.
- **Session Tracking**: Automatically logs completed sessions.

### 2. Task Management
- **Tasks and Subtasks**: Organize your work into tasks and subtasks with weighted progress.
- **Progress Tracking**: Visualize your progress with a progress bar.
- **Task Actions**: Add, edit, delete, and toggle task completion.

### 3. Calendar
- **Event Management**: Add, edit, and view events with color-coded categories (e.g., Exam, Project, Birthday).
- **Navigation**: Easily navigate between months.

### 4. Reports
- **Daily and Weekly Reports**: View your productivity stats for today or the past week.
- **Custom Range**: Generate reports for a custom date range.

### 5. Gamified Rewards
- **Coins and XP**: Earn coins and XP by completing focus sessions and tasks.
- **Inventory**: Spend coins to unlock items like hats and pet slimes for your avatar.
- **Avatar Customization**: Visualize your unlocked items on your avatar in the game.

## File Structure

```
productivity_game/
├── data.json       # Stores user data (tasks, sessions, inventory, etc.)
├── pg_game.py      # Pygame-based reward world
├── shared.py       # Shared utilities for data handling
├── tk_app.py       # Tkinter-based productivity app
```

## How It Works

### Data Management
- All user data is stored in `data.json`.
- The `shared.py` module provides utility functions for loading, saving, and updating the data.

### Reward World
- The `pg_game.py` file contains a Pygame-based interactive world where users can spend coins to unlock items.
- Items purchased (e.g., hats, pet slimes) are displayed on the avatar.

### Productivity App
- The `tk_app.py` file is a Tkinter-based GUI application with tabs for Pomodoro, Tasks, Calendar, and Reports.
- The app integrates with the reward system, allowing users to earn coins and XP for their productivity.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/suwarna-wave/productivity_game.git
   cd productivity_game
   ```

2. Install dependencies:
   ```bash
   pip install pygame
   ```

3. Run the application:
   ```bash
   python tk_app.py
   ```

## Usage

1. Launch the app using `python tk_app.py`.
2. Use the Pomodoro tab to start focus sessions and earn rewards.
3. Manage your tasks and subtasks in the Tasks tab.
4. Add and view events in the Calendar tab.
5. View your productivity stats in the Reports tab.
6. Open the Reward World to spend your coins and customize your avatar.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to improve the project.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

- **Pygame**: For creating the interactive reward world.
- **Tkinter**: For the GUI-based productivity app.
- **Community**: For inspiration and feedback.

---

Stay productive and have fun with the Productivity Game!
