# PowerWatch - Smart Energy Management System

![energyInsights](https://github.com/enharukalo/powerwatch/assets/28190290/08652b24-8182-412f-af85-7137dcc81ea2)

PowerWatch is a term project for the Database Management Systems course. The main scope of the project is to manage and visualize energy data. It is developed in Python using the PyQt6 library for GUI purposes and the Matplotlib library for displaying graphs.

## Installation

To install the project, you need to have Python 3.6 or higher. You can install the required packages using the following command:

```sh
pip install -r requirements.txt
```

## Database Setup

The project uses MySQL for data storage. The `energy.sql` file contains sample data for the term project. To setup the database, you need to have MySQL installed and setup a database named 'energy'. The credentials used in the project are:

- Username: root
- Password: mysql1234

You can change these credentials in the `create_connection` function in the `src/main.py` file.

## Usage

You can run the project using the following command:

```sh
python src/main.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms of the MIT license. See the [LICENSE](LICENSE) file for details.
