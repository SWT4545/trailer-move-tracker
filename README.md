# 🚛 Trailer Move Tracker

A comprehensive Streamlit web application for tracking trailer moves with automatic mileage calculation, driver management, and financial tracking.

## ✨ Features

- **Password Protected Access**: Secure your data with built-in authentication
- **Full CRUD Operations**: Create, Read, Update, and Delete all data
- **Smart Mileage System**:
  - Manual entry with caching for future use
  - Google Maps Distance Matrix API integration
  - Automatic round-trip calculations
- **Dynamic Data Entry**:
  - Add new locations on-the-fly during move entry
  - Add new drivers without leaving the form
  - Smart dropdowns with "Add New" options
- **Excel Import/Export**:
  - Import existing data from Excel files
  - Export all data to formatted Excel workbooks
  - Maintain full editability after import
- **Dashboard Features**:
  - Color-coded status (green for paid moves)
  - Summary statistics and metrics
  - Quick filters for unpaid, in-progress, and completed moves
- **Mobile-Optimized**: Large touch targets and responsive design for use while driving

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or download this repository**:
   ```bash
   git clone https://github.com/yourusername/trailer-move-tracker.git
   cd trailer-move-tracker
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure secrets**:
   - Edit `.streamlit/secrets.toml`
   - Set your password: `password = "your_secure_password"`
   - (Optional) Add Google Maps API key: `GOOGLE_MAPS_API_KEY = "your_api_key"`

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

5. **Access the app**:
   - Open your browser to `http://localhost:8501`
   - Enter your password to access the application

## 🔧 Configuration

### Setting Up Password Protection

Edit `.streamlit/secrets.toml`:
```toml
password = "your_secure_password_here"
```

### Google Maps API Setup (Optional)

1. Get an API key from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Enable the **Distance Matrix API** for your project
3. Add the key to `.streamlit/secrets.toml`:
   ```toml
   GOOGLE_MAPS_API_KEY = "your_api_key_here"
   ```

The app works perfectly without the API key - you'll just need to enter mileage manually.

## 📁 Data Import

### Importing from Excel

1. Navigate to the **Import/Export** page
2. Upload your Excel file with these sheets:
   - **Trailer Move Tracker** or **Trailer Moves**: Main moves data
   - **Locations**: Location names and addresses
   - **Drivers**: Driver information

### Expected Excel Columns

**Trailer Moves Sheet**:
- New Trailer, Pickup Location, Destination
- Old Trailer, Old Pickup, Old Destination
- Assigned Driver, Date Assigned, Completion Date
- Received PPW, Processed, Paid
- Miles, Rate, Factor Fee, Load Pay
- Comments

**Locations Sheet**:
- Location Title, Location Address

**Drivers Sheet**:
- Driver Name, Truck Number, Company Name
- Company Address, DOT, MC, Insurance

## 🌐 Deployment Options

### Option 1: Streamlit Community Cloud (Free)

1. Push your code to GitHub (make sure `.streamlit/secrets.toml` is in `.gitignore`)
2. Sign up at [share.streamlit.io](https://share.streamlit.io)
3. Deploy your app from your GitHub repository
4. Add secrets in Streamlit Cloud settings:
   - `password = "your_password"`
   - `GOOGLE_MAPS_API_KEY = "your_api_key"` (optional)

### Option 2: Local Network Deployment

Run on your local network for maximum privacy:

```bash
streamlit run app.py --server.address 0.0.0.0
```

Access from any device on your network using your computer's IP address:
`http://192.168.1.xxx:8501`

### Option 3: Secure Remote Access with ngrok

1. Install ngrok: [ngrok.com](https://ngrok.com)
2. Run your Streamlit app: `streamlit run app.py`
3. In another terminal: `ngrok http 8501`
4. Access your app from anywhere using the ngrok URL

## 📱 Mobile Usage Tips

- The app is optimized for mobile browsers
- Use landscape mode for better table viewing
- All forms have large touch targets
- Quick-add options minimize typing
- Mileage auto-calculation saves time on the road

## 🔒 Security & Privacy

- All data is stored locally in SQLite database
- Password protection prevents unauthorized access
- Use `.gitignore` to keep sensitive data out of version control
- For maximum privacy, deploy locally or on your own server
- Regular backups are recommended (see Import/Export → Backup/Restore)

## 🛠️ Troubleshooting

### Common Issues

**"Password incorrect" error**:
- Check `.streamlit/secrets.toml` for the correct password
- Ensure the file is properly formatted (TOML syntax)

**Google Maps not working**:
- Verify your API key is correct
- Check that Distance Matrix API is enabled in Google Cloud Console
- Ensure you have billing enabled on your Google Cloud account

**Import failing**:
- Check that your Excel file has the expected column names
- Download the sample template from Import/Export page
- Ensure dates are in a recognizable format

**Database errors**:
- Make sure the `data/` directory exists and is writable
- Try creating a backup and starting fresh

## 📊 Features Walkthrough

### Dashboard
- View all moves with color coding (green = paid)
- Filter by status, driver, and date range
- Quick statistics overview
- Inline editing capabilities

### Add New Move
- Smart location dropdowns with "Add New" option
- Automatic mileage calculation or manual entry
- Save routes for future use
- Real-time load pay calculation

### Manage Locations
- View all locations in editable table
- Add new locations with addresses
- Delete unused locations

### Manage Drivers
- Complete driver information management
- Track company details, DOT, MC numbers
- Easy addition during move entry

### Manage Mileage
- View and edit cached routes
- Manual route addition
- Automatic caching from move entries

### Import/Export
- Excel import with smart column mapping
- Full data export to Excel
- Database backup and restore
- Sample template download

## 🤝 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review the in-app help tooltips
3. Create an issue on GitHub

## 📄 License

This project is provided as-is for personal and commercial use.

## 🙏 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io) - The fastest way to build data apps
- [Google Maps Platform](https://developers.google.com/maps) - For distance calculations
- [SQLite](https://sqlite.org) - Reliable local database
- [Pandas](https://pandas.pydata.org) - Data manipulation and analysis