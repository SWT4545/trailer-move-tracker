# Smith & Williams Trucking - Trailer Swap Management System

## 🚛 Overview
A comprehensive web-based trailer swap management system designed for Smith & Williams Trucking operations. The system streamlines trailer swaps between Fleet Memphis and customer locations with role-based access, automated mileage calculation, and integrated payment processing.

## ✨ Features

### Core Functionality
- **Trailer Swap Management**: Track NEW and OLD trailer swaps between locations
- **Automated Mileage Calculation**: Google Maps integration for accurate distance tracking
- **Multi-Photo POD Upload**: Up to 10 photos for NEW trailers, 2 for OLD trailers
- **Payment Processing**: Complete workflow from client billing to driver payments
- **Role-Based Access Control**: Business Administrator, Operations Coordinator, and Driver roles

### Advanced Features
- **Vernon IT Bot**: Automated system maintenance and monitoring
- **Mobile-Friendly**: Responsive design for phones and tablets
- **No-Login POD Upload**: Drivers can upload documentation via secure links
- **Real-Time Driver Availability**: Track driver status and assignments
- **Company Branding**: Customizable company information and signatures

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Streamlit account (for deployment)
- Google Maps API key (optional, for mileage calculation)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/trailer-move-tracker.git
cd trailer-move-tracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## 🔐 Default Credentials

### Business Administrator
- Username: `admin`
- Password: `admin123`
- Full system access including financial management

### Operations Coordinator
- Username: `coordinator`
- Password: `coord123`
- Manage trailers, drivers, and moves

### Driver
- Username: `driver1`
- Password: `drive123`
- View assignments and upload PODs

## 📱 Mobile POD Upload

Drivers receive a unique link for each move that allows them to upload:
- POD document (Bill of Lading)
- NEW Trailer Photos (up to 10 total)
  - 5 photos at pickup (Fleet Memphis)
  - 5 photos at delivery (Customer location)
- OLD Trailer Photos (up to 2 total)
  - 1 photo at pickup (Customer location)
  - 1 photo at delivery (Fleet Memphis)

## 🤖 Vernon IT Bot

The system includes Vernon, an automated IT support specialist that:
- Monitors system health in real-time
- Automatically fixes common issues
- Performs scheduled maintenance
- Validates system after upgrades
- Provides diagnostic reports

Access Vernon through the IT Support menu (Admin only).

## 🛠️ Configuration

### Environment Variables
```bash
GOOGLE_MAPS_API_KEY=your_api_key_here
```

### Company Settings
Company information can be configured through the System Admin menu:
- Company name, email, phone
- DOT/MC numbers
- Email signatures
- Branding colors

## 📊 Database Schema

The system uses SQLite with the following main tables:
- `users`: System users and authentication
- `trailers`: Trailer pair inventory
- `drivers`: Driver information and status
- `moves`: Trailer swap assignments
- `locations`: Customer locations
- `mileage_cache`: Cached distance calculations
- `activity_log`: System activity tracking

## 🚀 Deployment

### Streamlit Cloud

1. Push to GitHub:
```bash
git add .
git commit -m "Deploy trailer management system"
git push origin main
```

2. Connect to Streamlit Cloud:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Deploy the app

### Local Deployment

For local network deployment:
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

## 📋 Workflow

1. **Admin/Coordinator**: Add trailer pairs to inventory
2. **Coordinator**: Create moves and assign to drivers
3. **System**: Generate unique POD upload link
4. **Coordinator**: Send assignment message to driver
5. **Driver**: Complete swap and upload POD/photos
6. **Admin**: Process payments through factoring
7. **System**: Track payment status and driver earnings

## 🔧 Maintenance

Vernon IT Bot automatically handles:
- Database optimization
- Session cleanup
- File system checks
- Dependency validation
- Resource monitoring

Manual maintenance available through IT Support panel.

## 📝 License

Proprietary software for Smith & Williams Trucking.

## 📞 Support

For technical support, contact:
- Email: Dispatch@smithwilliamstrucking.com
- Phone: (901) 555-SHIP

---

**"Your cargo. Our mission. Moving forward."**

© 2024 Smith & Williams Trucking. All rights reserved.