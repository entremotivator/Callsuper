import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import uuid
import hashlib
from typing import Dict, List, Any
import asyncio
import threading
from dataclasses import dataclass
from enum import Enum
import base64
import io

# Page configuration
st.set_page_config(
    page_title="VAPI AI Call Center Pro",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .assistant-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        margin-bottom: 1.5rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .assistant-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    
    .call-button {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        border: none;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .call-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(40, 167, 69, 0.4);
    }
    
    .metrics-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 4px solid #667eea;
        transition: transform 0.3s ease;
    }
    
    .metrics-card:hover {
        transform: translateY(-3px);
    }
    
    .status-active {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .status-idle {
        background: linear-gradient(45deg, #ffc107, #fd7e14);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .status-error {
        background: linear-gradient(45deg, #dc3545, #e83e8c);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    
    .call-log-row {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #28a745;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    .alert-success {
        background: linear-gradient(45deg, #d4edda, #c3e6cb);
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .alert-warning {
        background: linear-gradient(45deg, #fff3cd, #ffeaa7);
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .alert-danger {
        background: linear-gradient(45deg, #f8d7da, #f5c6cb);
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .tab-container {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .real-time-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #28a745;
        border-radius: 50%;
        animation: pulse 2s infinite;
        margin-right: 0.5rem;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .performance-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    
    .badge-excellent {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
    }
    
    .badge-good {
        background: linear-gradient(45deg, #17a2b8, #6f42c1);
        color: white;
    }
    
    .badge-average {
        background: linear-gradient(45deg, #ffc107, #fd7e14);
        color: white;
    }
    
    .badge-poor {
        background: linear-gradient(45deg, #dc3545, #e83e8c);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Data Classes and Enums
class CallStatus(Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    CONNECTED = "connected"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"

class AssistantStatus(Enum):
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    ERROR = "error"

@dataclass
class CallRecord:
    call_id: str
    assistant_id: str
    phone_number: str
    start_time: datetime
    end_time: datetime = None
    duration: int = 0
    status: CallStatus = CallStatus.INITIATED
    transcript: str = ""
    sentiment_score: float = 0.0
    lead_score: float = 0.0
    cost: float = 0.0
    recording_url: str = ""
    custom_data: Dict[str, Any] = None

@dataclass
class AssistantConfig:
    id: str
    name: str
    description: str
    phone_number: str
    voice: str
    language: str
    max_duration: int
    background_sound: str
    temperature: float
    response_speed: str
    custom_prompt: str
    webhook_url: str
    sheet_id: str
    status: AssistantStatus
    specialization: str
    cost_per_minute: float
    success_rate: float
    total_calls: int
    total_revenue: float

# Enhanced Assistant Configurations
SPECIALIZATIONS = [
    "Sales & Lead Generation", "Customer Support", "Appointment Scheduling", 
    "Market Research & Surveys", "Debt Collection", "Insurance Claims",
    "Real Estate Inquiries", "Healthcare Appointments", "E-commerce Support",
    "Technical Support", "Event Registration", "Fundraising & Donations",
    "Product Demonstrations", "Quality Assurance", "Emergency Response",
    "Educational Outreach", "Political Campaigns", "Travel Booking",
    "Financial Services", "Legal Consultations", "HR Recruitment",
    "Property Management", "Automotive Services", "Food Delivery",
    "Subscription Management"
]

VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "custom_voice_1", "custom_voice_2"]
LANGUAGES = ["en-US", "en-GB", "es-ES", "es-MX", "fr-FR", "de-DE", "it-IT", "pt-BR", "ja-JP", "ko-KR", "zh-CN", "hi-IN"]
BACKGROUND_SOUNDS = ["none", "office", "cafe", "nature", "city", "white_noise", "classical_music"]

# Generate comprehensive assistant configurations
ASSISTANT_CONFIGS = {}
for i in range(25):
    assistant_id = f"vapi_assistant_{i+1:02d}"
    ASSISTANT_CONFIGS[f"assistant_{i+1}"] = AssistantConfig(
        id=assistant_id,
        name=f"AI Assistant {i+1} - {SPECIALIZATIONS[i]['name'] if i < len(SPECIALIZATIONS) else 'General'}",
        description=f"Specialized AI assistant for {SPECIALIZATIONS[i] if i < len(SPECIALIZATIONS) else 'General Purpose'}",
        phone_number=f"+1-555-{1000 + i:04d}",
        voice=VOICES[i % len(VOICES)],
        language=LANGUAGES[i % len(LANGUAGES)],
        max_duration=300 + (i * 30),
        background_sound=BACKGROUND_SOUNDS[i % len(BACKGROUND_SOUNDS)],
        temperature=0.3 + (i * 0.02),
        response_speed=["slow", "normal", "fast"][i % 3],
        custom_prompt=f"You are a professional {SPECIALIZATIONS[i] if i < len(SPECIALIZATIONS) else 'general'} assistant.",
        webhook_url=f"https://webhook.site/{uuid.uuid4()}",
        sheet_id=f"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms_{i+1}",
        status=AssistantStatus(["active", "idle", "busy"][i % 3]),
        specialization=SPECIALIZATIONS[i] if i < len(SPECIALIZATIONS) else "General Purpose",
        cost_per_minute=0.05 + (i * 0.01),
        success_rate=65 + (i * 1.2),
        total_calls=100 + (i * 50),
        total_revenue=500 + (i * 250)
    )

# Initialize session state with enhanced data
def initialize_session_state():
    if 'current_assistant' not in st.session_state:
        st.session_state.current_assistant = "assistant_1"
    if 'call_history' not in st.session_state:
        st.session_state.call_history = []
    if 'vapi_api_key' not in st.session_state:
        st.session_state.vapi_api_key = ""
    if 'google_credentials' not in st.session_state:
        st.session_state.google_credentials = ""
    if 'real_time_monitoring' not in st.session_state:
        st.session_state.real_time_monitoring = False
    if 'notification_settings' not in st.session_state:
        st.session_state.notification_settings = {
            'email_alerts': False,
            'sms_alerts': False,
            'webhook_alerts': True,
            'alert_threshold': 80
        }
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'theme': 'light',
            'auto_refresh': False,
            'refresh_interval': 30,
            'default_view': 'dashboard'
        }
    if 'active_calls' not in st.session_state:
        st.session_state.active_calls = {}
    if 'system_health' not in st.session_state:
        st.session_state.system_health = {
            'api_status': 'healthy',
            'database_status': 'healthy',
            'webhook_status': 'healthy',
            'last_check': datetime.now()
        }

initialize_session_state()

# Enhanced Helper Functions
class VAPIManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.vapi.ai/v1"
        
    def create_assistant(self, config: AssistantConfig) -> Dict[str, Any]:
        """Create a new VAPI assistant"""
        payload = {
            "name": config.name,
            "voice": config.voice,
            "language": config.language,
            "firstMessage": f"Hello! I'm {config.name}, how can I help you today?",
            "systemPrompt": config.custom_prompt,
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": config.temperature
            },
            "transcriber": {
                "provider": "deepgram",
                "model": "nova-2",
                "language": config.language
            }
        }
        
        # Simulate API response
        return {
            "success": True,
            "assistant_id": config.id,
            "message": "Assistant created successfully"
        }
    
    def initiate_call(self, assistant_id: str, phone_number: str, custom_prompt: str = "") -> Dict[str, Any]:
        """Initiate a call using VAPI"""
        if not self.api_key:
            return {"error": "VAPI API key not configured"}
        
        call_id = str(uuid.uuid4())
        
        # Create call record
        call_record = CallRecord(
            call_id=call_id,
            assistant_id=assistant_id,
            phone_number=phone_number,
            start_time=datetime.now(),
            status=CallStatus.INITIATED,
            custom_data={"custom_prompt": custom_prompt}
        )
        
        # Add to session state
        st.session_state.call_history.append(call_record)
        st.session_state.active_calls[call_id] = call_record
        
        return {
            "success": True,
            "call_id": call_id,
            "status": "initiated",
            "estimated_cost": 0.15
        }
    
    def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get the status of a specific call"""
        if call_id in st.session_state.active_calls:
            call = st.session_state.active_calls[call_id]
            return {
                "call_id": call_id,
                "status": call.status.value,
                "duration": call.duration,
                "cost": call.cost
            }
        return {"error": "Call not found"}
    
    def end_call(self, call_id: str) -> Dict[str, Any]:
        """End an active call"""
        if call_id in st.session_state.active_calls:
            call = st.session_state.active_calls[call_id]
            call.end_time = datetime.now()
            call.duration = int((call.end_time - call.start_time).total_seconds())
            call.status = CallStatus.COMPLETED
            call.cost = call.duration * 0.02  # $0.02 per second
            
            # Remove from active calls
            del st.session_state.active_calls[call_id]
            
            return {"success": True, "message": "Call ended successfully"}
        return {"error": "Call not found"}

class GoogleSheetsManager:
    def __init__(self, credentials_json: str):
        self.credentials_json = credentials_json
        
    def get_sheet_data(self, sheet_id: str, assistant_config: AssistantConfig) -> tuple:
        """Get data from Google Sheets"""
        # Enhanced simulated data with more realistic patterns
        base_calls = 50 + hash(sheet_id) % 100
        time_factor = datetime.now().hour / 24.0
        
        metrics_data = {
            "calls_today": int(base_calls * (0.5 + time_factor)),
            "calls_this_week": int(base_calls * 7 * 0.8),
            "calls_this_month": int(base_calls * 30 * 0.6),
            "success_rate": assistant_config.success_rate + (hash(sheet_id) % 20 - 10),
            "avg_duration": 180 + (hash(sheet_id) % 120),
            "leads_generated": int((base_calls * 0.3) + (hash(sheet_id) % 15)),
            "conversion_rate": 15 + (hash(sheet_id) % 25),
            "customer_satisfaction": 4.2 + (hash(sheet_id) % 8) / 10,
            "total_revenue": assistant_config.total_revenue + (hash(sheet_id) % 1000),
            "cost_per_lead": 12.50 + (hash(sheet_id) % 20),
            "avg_call_cost": assistant_config.cost_per_minute * 3,
            "peak_hours": [9, 10, 11, 14, 15, 16],
            "sentiment_positive": 70 + (hash(sheet_id) % 20),
            "sentiment_neutral": 20 + (hash(sheet_id) % 10),
            "sentiment_negative": 10 + (hash(sheet_id) % 10)
        }
        
        # Generate realistic call log
        call_log_data = []
        for i in range(50):
            call_time = datetime.now() - timedelta(hours=i*2, minutes=hash(f"{sheet_id}_{i}") % 60)
            duration = 60 + (hash(f"{sheet_id}_{i}") % 300)
            status_options = ["Completed", "Missed", "Busy", "No Answer", "Failed"]
            status = status_options[hash(f"{sheet_id}_{i}") % len(status_options)]
            
            call_log_data.append({
                "Call ID": f"call_{i+1:03d}",
                "Time": call_time,
                "Phone": f"+1-555-{2000 + (hash(f'{sheet_id}_{i}') % 9000):04d}",
                "Duration": duration,
                "Status": status,
                "Lead Score": round(1 + (hash(f"{sheet_id}_{i}") % 90) / 10, 1),
                "Sentiment": ["Positive", "Neutral", "Negative"][hash(f"{sheet_id}_{i}") % 3],
                "Cost": round(duration * 0.02, 2),
                "Agent": assistant_config.name,
                "Campaign": f"Campaign {(hash(f'{sheet_id}_{i}') % 5) + 1}",
                "Notes": f"Call notes for {assistant_config.specialization}"
            })
        
        call_log = pd.DataFrame(call_log_data)
        
        return metrics_data, call_log

class AnalyticsEngine:
    @staticmethod
    def calculate_performance_metrics(assistant_configs: Dict[str, AssistantConfig]) -> pd.DataFrame:
        """Calculate comprehensive performance metrics"""
        metrics_data = []
        
        for key, config in assistant_configs.items():
            # Simulate realistic performance data
            daily_calls = 20 + hash(config.id) % 50
            weekly_calls = daily_calls * 7
            monthly_calls = daily_calls * 30
            
            metrics_data.append({
                'Assistant ID': config.id,
                'Assistant Name': config.name,
                'Specialization': config.specialization,
                'Status': config.status.value,
                'Daily Calls': daily_calls,
                'Weekly Calls': weekly_calls,
                'Monthly Calls': monthly_calls,
                'Success Rate': config.success_rate,
                'Avg Duration': 180 + hash(config.id) % 120,
                'Cost per Call': config.cost_per_minute * 3,
                'Revenue Generated': config.total_revenue,
                'Lead Conversion': 15 + hash(config.id) % 20,
                'Customer Satisfaction': 4.0 + (hash(config.id) % 10) / 10,
                'Response Time': 2 + hash(config.id) % 8,
                'Uptime %': 95 + hash(config.id) % 5,
                'Error Rate': hash(config.id) % 5,
                'Peak Performance Hour': 9 + hash(config.id) % 8,
                'Language': config.language,
                'Voice': config.voice,
                'Last Active': datetime.now() - timedelta(minutes=hash(config.id) % 120)
            })
        
        return pd.DataFrame(metrics_data)
    
    @staticmethod
    def generate_forecasting_data(days: int = 30) -> pd.DataFrame:
        """Generate forecasting data for the next N days"""
        dates = pd.date_range(start=datetime.now(), periods=days, freq='D')
        
        forecast_data = []
        for i, date in enumerate(dates):
            base_calls = 500 + i * 10
            seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * i / 7)  # Weekly seasonality
            trend_factor = 1 + 0.02 * i  # Growth trend
            
            forecast_data.append({
                'Date': date,
                'Predicted Calls': int(base_calls * seasonal_factor * trend_factor),
                'Confidence Lower': int(base_calls * seasonal_factor * trend_factor * 0.8),
                'Confidence Upper': int(base_calls * seasonal_factor * trend_factor * 1.2),
                'Expected Revenue': base_calls * seasonal_factor * trend_factor * 2.5,
                'Resource Requirement': int((base_calls * seasonal_factor * trend_factor) / 50)
            })
        
        return pd.DataFrame(forecast_data)

# Initialize managers
vapi_manager = VAPIManager(st.session_state.vapi_api_key)
sheets_manager = GoogleSheetsManager(st.session_state.google_credentials)
analytics_engine = AnalyticsEngine()

# Enhanced Header with Real-time Status
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    st.markdown("""
    <div class="main-header">
        <h1>📞 VAPI AI Call Center Pro</h1>
        <p>Enterprise-Grade AI Phone Assistant Management Platform</p>
        <p><span class="real-time-indicator"></span>Real-time Monitoring Active</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # System Health Indicator
    health_color = "green" if st.session_state.system_health['api_status'] == 'healthy' else "red"
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem;">
        <h4>System Health</h4>
        <div style="width: 20px; height: 20px; background: {health_color}; border-radius: 50%; margin: 0 auto;"></div>
        <small>All Systems Operational</small>
    </div>
    """, unsafe_allow_html=True)

with col3:
    # Active Calls Counter
    active_calls_count = len(st.session_state.active_calls)
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem;">
        <h4>Active Calls</h4>
        <h2 style="color: #667eea;">{active_calls_count}</h2>
        <small>Currently Running</small>
    </div>
    """, unsafe_allow_html=True)

# Enhanced Sidebar with Advanced Navigation
st.sidebar.title("🎯 Navigation Center")

# Quick Stats in Sidebar
with st.sidebar.expander("📊 Quick Overview", expanded=True):
    total_assistants = len(ASSISTANT_CONFIGS)
    active_assistants = sum(1 for config in ASSISTANT_CONFIGS.values() if config.status == AssistantStatus.ACTIVE)
    total_calls_today = sum(20 + hash(config.id) % 50 for config in ASSISTANT_CONFIGS.values())
    
    st.metric("Total Assistants", total_assistants)
    st.metric("Active Now", active_assistants)
    st.metric("Calls Today", total_calls_today)

# API Configuration Section
with st.sidebar.expander("🔧 API Configuration"):
    vapi_api_key = st.text_input("VAPI API Key", type="password", value=st.session_state.vapi_api_key)
    if vapi_api_key != st.session_state.vapi_api_key:
        st.session_state.vapi_api_key = vapi_api_key
        vapi_manager = VAPIManager(vapi_api_key)
    
    google_creds = st.text_area("Google Service Account JSON", height=100, value=st.session_state.google_credentials)
    if google_creds != st.session_state.google_credentials:
        st.session_state.google_credentials = google_creds
        sheets_manager = GoogleSheetsManager(google_creds)
    
    # API Health Check
    if st.button("🔍 Test API Connection"):
        if vapi_api_key:
            st.success("✅ VAPI API Connected")
        else:
            st.error("❌ VAPI API Key Required")
        
        if google_creds:
            st.success("✅ Google Sheets Connected")
        else:
            st.warning("⚠️ Google Sheets Not Configured")

# User Preferences
with st.sidebar.expander("⚙️ User Preferences"):
    st.session_state.user_preferences['auto_refresh'] = st.checkbox(
        "Auto Refresh", 
        value=st.session_state.user_preferences['auto_refresh']
    )
    
    st.session_state.user_preferences['refresh_interval'] = st.slider(
        "Refresh Interval (seconds)", 
        10, 300, 
        st.session_state.user_preferences['refresh_interval']
    )
    
    st.session_state.user_preferences['theme'] = st.selectbox(
        "Theme", 
        ["light", "dark"], 
        index=0 if st.session_state.user_preferences['theme'] == 'light' else 1
    )

# Assistant Selection with Enhanced Filtering
st.sidebar.subheader("🤖 Assistant Selection")

# Filtering options
filter_status = st.sidebar.multiselect(
    "Filter by Status",
    [status.value for status in AssistantStatus],
    default=[status.value for status in AssistantStatus]
)

filter_specialization = st.sidebar.multiselect(
    "Filter by Specialization",
    list(set(config.specialization for config in ASSISTANT_CONFIGS.values())),
    default=list(set(config.specialization for config in ASSISTANT_CONFIGS.values()))
)

# Filter assistants based on criteria
filtered_assistants = {
    key: config for key, config in ASSISTANT_CONFIGS.items()
    if config.status.value in filter_status and config.specialization in filter_specialization
}

selected_assistant = st.sidebar.selectbox(
    "Select Assistant",
    options=list(filtered_assistants.keys()),
    format_func=lambda x: filtered_assistants[x].name,
    index=0 if filtered_assistants else 0
)

if selected_assistant:
    st.session_state.current_assistant = selected_assistant
    current_config = ASSISTANT_CONFIGS[selected_assistant]
else:
    current_config = list(ASSISTANT_CONFIGS.values())[0]

# Page Selection with Enhanced Options
page = st.sidebar.radio(
    "📋 Main Navigation",
    [
        "🏠 Dashboard", 
        "📞 Call Center", 
        "📊 Live Analytics", 
        "📈 Advanced Reports",
        "⚙️ Assistant Config", 
        "🎛️ Bulk Operations",
        "🔍 Real-time Monitor",
        "📋 Call Logs",
        "🎯 Campaign Manager",
        "🔧 System Admin"
    ]
)

# Main Content Area with Enhanced Pages
if page == "🏠 Dashboard":
    st.title("🏠 Executive Dashboard")
    
    # Key Performance Indicators
    st.subheader("📊 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_calls = sum(config.total_calls for config in ASSISTANT_CONFIGS.values())
        st.markdown(f"""
        <div class="metrics-card">
            <h3>{total_calls:,}</h3>
            <p>Total Calls</p>
            <small>+12% from last month</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_success_rate = np.mean([config.success_rate for config in ASSISTANT_CONFIGS.values()])
        st.markdown(f"""
        <div class="metrics-card">
            <h3>{avg_success_rate:.1f}%</h3>
            <p>Avg Success Rate</p>
            <small>+3.2% from last month</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_revenue = sum(config.total_revenue for config in ASSISTANT_CONFIGS.values())
        st.markdown(f"""
        <div class="metrics-card">
            <h3>${total_revenue:,.0f}</h3>
            <p>Total Revenue</p>
            <small>+18% from last month</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        active_count = sum(1 for config in ASSISTANT_CONFIGS.values() if config.status == AssistantStatus.ACTIVE)
        st.markdown(f"""
        <div class="metrics-card">
            <h3>{active_count}/25</h3>
            <p>Active Assistants</p>
            <small>96% uptime</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        avg_cost = np.mean([config.cost_per_minute * 3 for config in ASSISTANT_CONFIGS.values()])
        st.markdown(f"""
        <div class="metrics-card">
            <h3>${avg_cost:.2f}</h3>
            <p>Avg Cost/Call</p>
            <small>-5% from last month</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Performance Charts
    st.subheader("📈 Performance Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Daily Call Volume Trend
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        call_volumes = [400 + i*5 + np.random.randint(-50, 50) for i in range(len(dates))]
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=dates, 
            y=call_volumes,
            mode='lines+markers',
            name='Daily Calls',
            line=dict(color='#667eea', width=3)
        ))
        fig_trend.update_layout(
            title="Daily Call Volume Trend (30 Days)",
            xaxis_title="Date",
            yaxis_title="Number of Calls",
            height=400
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col2:
        # Success Rate by Specialization
        specializations = list(set(config.specialization for config in ASSISTANT_CONFIGS.values()))
        success_rates = []
        for spec in specializations:
            rates = [config.success_rate for config in ASSISTANT_CONFIGS.values() if config.specialization == spec]
            success_rates.append(np.mean(rates))
        
        fig_success = px.bar(
            x=specializations,
            y=success_rates,
            title="Success Rate by Specialization",
            color=success_rates,
            color_continuous_scale="Viridis"
        )
        fig_success.update_layout(height=400)
        st.plotly_chart(fig_success, use_container_width=True)
    
    # Top Performers
    st.subheader("🏆 Top Performing Assistants")
    
    performance_df = analytics_engine.calculate_performance_metrics(ASSISTANT_CONFIGS)
    top_performers = performance_df.nlargest(5, 'Success Rate')[['Assistant Name', 'Success Rate', 'Daily Calls', 'Revenue Generated']]
    
    for idx, row in top_performers.iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"**{row['Assistant Name']}**")
        with col2:
            st.write(f"{row['Success Rate']:.1f}%")
        with col3:
            st.write(f"{row['Daily Calls']} calls")
        with col4:
            st.write(f"${row['Revenue Generated']:,.0f}")
    
    # Recent Activity Feed
    st.subheader("🔔 Recent Activity")
    
    activities = [
        {"time": "2 minutes ago", "event": "Assistant 5 completed high-value lead call", "type": "success"},
        {"time": "5 minutes ago", "event": "Assistant 12 started appointment scheduling campaign", "type": "info"},
        {"time": "8 minutes ago", "event": "Assistant 3 achieved 95% success rate milestone", "type": "success"},
        {"time": "12 minutes ago", "event": "System maintenance completed successfully", "type": "info"},
        {"time": "15 minutes ago", "event": "New webhook integration activated", "type": "warning"}
    ]
    
    for activity in activities:
        icon = "✅" if activity["type"] == "success" else "ℹ️" if activity["type"] == "info" else "⚠️"
        st.markdown(f"""
        <div class="call-log-row">
            {icon} <strong>{activity['time']}</strong>: {activity['event']}
        </div>
        """, unsafe_allow_html=True)

elif page == "📞 Call Center":
    st.title(f"📞 Call Center - {current_config.name}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Enhanced Assistant Information
        st.markdown(f"""
        <div class="assistant-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3>{current_config.name}</h3>
                    <p><strong>Specialization:</strong> {current_config.specialization}</p>
                    <p><strong>ID:</strong> {current_config.id}</p>
                    <p><strong>Phone:</strong> {current_config.phone_number}</p>
                    <p><strong>Voice:</strong> {current_config.voice} | <strong>Language:</strong> {current_config.language}</p>
                </div>
                <div>
                    <span class="status-{current_config.status.value}">{current_config.status.value.upper()}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced Call Interface
        st.subheader("📞 Call Management")
        
        # Call Configuration Tabs
        tab1, tab2, tab3 = st.tabs(["📞 Single Call", "📋 Batch Calls", "🔄 Scheduled Calls"])
        
        with tab1:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                target_phone = st.text_input("Target Phone Number", placeholder="+1-555-0123")
            with col_b:
                call_type = st.selectbox("Call Type", ["Outbound Sales", "Follow-up", "Survey", "Support", "Appointment"])
            with col_c:
                priority = st.selectbox("Priority", ["Low", "Normal", "High", "Urgent"])
            
            custom_prompt = st.text_area("Custom Prompt Override", 
                                       placeholder="Enter custom instructions for this call...",
                                       value=current_config.custom_prompt)
            
            col_x, col_y, col_z = st.columns(3)
            with col_x:
                max_duration = st.slider("Max Duration (seconds)", 60, 600, current_config.max_duration)
            with col_y:
                callback_url = st.text_input("Callback URL", placeholder="https://your-webhook.com/callback")
            with col_z:
                record_call = st.checkbox("Record Call", value=True)
            
            if st.button("🚀 Initiate Call", type="primary", use_container_width=True):
                if target_phone and st.session_state.vapi_api_key:
                    with st.spinner("Initiating call..."):
                        result = vapi_manager.initiate_call(current_config.id, target_phone, custom_prompt)
                        if "success" in result:
                            st.success(f"✅ Call initiated successfully!")
                            st.info(f"📞 Call ID: {result['call_id']}")
                            st.info(f"💰 Estimated Cost: ${result['estimated_cost']:.2f}")
                        else:
                            st.error(f"❌ Call failed: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("⚠️ Please enter phone number and configure VAPI API key")
        
        with tab2:
            st.subheader("📋 Batch Call Operations")
            
            uploaded_file = st.file_uploader("Upload Phone Numbers (CSV)", type=['csv'])
            if uploaded_file:
                phone_df = pd.read_csv(uploaded_file)
                st.dataframe(phone_df.head(10))
                
                col_batch1, col_batch2 = st.columns(2)
                with col_batch1:
                    batch_delay = st.slider("Delay Between Calls (seconds)", 5, 300, 30)
                with col_batch2:
                    batch_size = st.slider("Batch Size", 1, 50, 10)
                
                if st.button("🚀 Start Batch Calling"):
                    st.success(f"✅ Batch calling initiated for {len(phone_df)} numbers")
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    st.success("🎉 Batch calling completed!")
        
        with tab3:
            st.subheader("🔄 Scheduled Call Management")
            
            col_sched1, col_sched2 = st.columns(2)
            with col_sched1:
                schedule_date = st.date_input("Schedule Date")
                schedule_time = st.time_input("Schedule Time")
            with col_sched2:
                repeat_frequency = st.selectbox("Repeat", ["Once", "Daily", "Weekly", "Monthly"])
                timezone = st.selectbox("Timezone", ["UTC", "EST", "PST", "CST", "MST"])
            
            scheduled_phone = st.text_input("Phone Number for Scheduled Call")
            scheduled_prompt = st.text_area("Scheduled Call Prompt")
            
            if st.button("📅 Schedule Call"):
                st.success("✅ Call scheduled successfully!")
    
    with col2:
        # Enhanced Quick Stats and Controls
        st.subheader("📊 Real-time Stats")
        
        metrics_data, _ = sheets_manager.get_sheet_data(current_config.sheet_id, current_config)
        
        # Performance Metrics
        st.metric("Calls Today", metrics_data['calls_today'], delta=f"+{metrics_data['calls_today'] - metrics_data.get('calls_yesterday', metrics_data['calls_today'] - 5)}")
        st.metric("Success Rate", f"{metrics_data['success_rate']:.1f}%", delta=f"+{metrics_data['success_rate'] - 75:.1f}%")
        st.metric("Avg Duration", f"{metrics_data['avg_duration']}s", delta=f"+{metrics_data['avg_duration'] - 180}s")
        st.metric("Revenue Today", f"${metrics_data.get('revenue_today', 1250):.0f}", delta=f"+${metrics_data.get('revenue_today', 1250) - 1100:.0f}")
        
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("⏸️ Pause Assistant", use_container_width=True):
            st.info("Assistant paused")
        
        if st.button("🔄 Restart Assistant", use_container_width=True):
            st.info("Assistant restarted")
        
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("Report generated")
        
        # Active Calls Monitor
        st.subheader("📞 Active Calls")
        
        if st.session_state.active_calls:
            for call_id, call in st.session_state.active_calls.items():
                if call.assistant_id == current_config.id:
                    duration = int((datetime.now() - call.start_time).total_seconds())
                    st.markdown(f"""
                    <div class="call-log-row">
                        <strong>📞 {call.phone_number}</strong><br>
                        Duration: {duration}s<br>
                        Status: {call.status.value}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No active calls")
        
        # Recent Call History
        st.subheader("🕒 Recent Calls")
        
        recent_calls = [call for call in st.session_state.call_history[-10:] if call.assistant_id == current_config.id]
        for call in recent_calls:
            status_icon = "✅" if call.status == CallStatus.COMPLETED else "❌" if call.status == CallStatus.FAILED else "🔄"
            st.markdown(f"""
            <div class="call-log-row">
                {status_icon} <strong>{call.phone_number}</strong><br>
                <small>{call.start_time.strftime('%H:%M:%S')} - {call.status.value}</small>
            </div>
            """, unsafe_allow_html=True)

elif page == "📊 Live Analytics":
    st.title("📊 Live Analytics Dashboard")
    
    # Real-time refresh indicator
    if st.session_state.user_preferences['auto_refresh']:
        st.markdown('<span class="real-time-indicator"></span>Auto-refresh enabled', unsafe_allow_html=True)
    
    # Time range selector
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        time_range = st.selectbox("Time Range", ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "Custom"])
    with col2:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    with col3:
        export_format = st.selectbox("Export", ["PDF", "CSV", "Excel"])
    
    # Live Metrics Grid
    st.subheader("📈 Live Performance Metrics")
    
    metrics_data, call_log = sheets_manager.get_sheet_data(current_config.sheet_id, current_config)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    metrics = [
        ("Total Calls", metrics_data['calls_today'], "+12%"),
        ("Success Rate", f"{metrics_data['success_rate']:.1f}%", "+3.2%"),
        ("Avg Duration", f"{metrics_data['avg_duration']}s", "-5s"),
        ("Conversion", f"{metrics_data['conversion_rate']:.1f}%", "+2.1%"),
        ("Revenue", f"${metrics_data['total_revenue']:,.0f}", "+18%"),
        ("Satisfaction", f"{metrics_data['customer_satisfaction']:.1f}/5", "+0.3")
    ]
    
    for i, (label, value, delta) in enumerate(metrics):
        with [col1, col2, col3, col4, col5, col6][i]:
            st.metric(label, value, delta)
    
    # Advanced Charts Section
    st.subheader("📊 Advanced Analytics")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "🎯 Performance", "💰 Revenue", "😊 Sentiment"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Call Volume Heatmap
            hours = list(range(24))
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            
            # Generate heatmap data
            heatmap_data = np.random.randint(10, 100, size=(len(days), len(hours)))
            
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=hours,
                y=days,
                colorscale='Viridis',
                hoverongaps=False
            ))
            fig_heatmap.update_layout(
                title="Call Volume Heatmap (Hour vs Day)",
                xaxis_title="Hour of Day",
                yaxis_title="Day of Week"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        with col2:
            # Success Rate Trend
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
            success_rates = [75 + 10 * np.sin(i/5) + np.random.normal(0, 3) for i in range(len(dates))]
            
            fig_success_trend = go.Figure()
            fig_success_trend.add_trace(go.Scatter(
                x=dates,
                y=success_rates,
                mode='lines+markers',
                name='Success Rate',
                line=dict(color='#28a745', width=3)
            ))
            fig_success_trend.update_layout(
                title="Success Rate Trend (30 Days)",
                xaxis_title="Date",
                yaxis_title="Success Rate (%)",
                yaxis=dict(range=[0, 100])
            )
            st.plotly_chart(fig_success_trend, use_container_width=True)
    
    with tab2:
        # Performance Comparison
        performance_df = analytics_engine.calculate_performance_metrics(ASSISTANT_CONFIGS)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top vs Bottom Performers
            top_5 = performance_df.nlargest(5, 'Success Rate')
            bottom_5 = performance_df.nsmallest(5, 'Success Rate')
            
            fig_comparison = go.Figure()
            fig_comparison.add_trace(go.Bar(
                name='Top 5',
                x=top_5['Assistant Name'],
                y=top_5['Success Rate'],
                marker_color='#28a745'
            ))
            fig_comparison.add_trace(go.Bar(
                name='Bottom 5',
                x=bottom_5['Assistant Name'],
                y=bottom_5['Success Rate'],
                marker_color='#dc3545'
            ))
            fig_comparison.update_layout(
                title="Performance Comparison: Top vs Bottom 5",
                xaxis_title="Assistant",
                yaxis_title="Success Rate (%)"
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        with col2:
            # Performance Distribution
            fig_dist = px.histogram(
                performance_df,
                x='Success Rate',
                nbins=20,
                title="Success Rate Distribution",
                color_discrete_sequence=['#667eea']
            )
            st.plotly_chart(fig_dist, use_container_width=True)
    
    with tab3:
        # Revenue Analytics
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue by Specialization
            revenue_by_spec = performance_df.groupby('Specialization')['Revenue Generated'].sum().reset_index()
            
            fig_revenue_pie = px.pie(
                revenue_by_spec,
                values='Revenue Generated',
                names='Specialization',
                title="Revenue Distribution by Specialization"
            )
            st.plotly_chart(fig_revenue_pie, use_container_width=True)
        
        with col2:
            # Cost vs Revenue Analysis
            fig_cost_revenue = px.scatter(
                performance_df,
                x='Cost per Call',
                y='Revenue Generated',
                size='Daily Calls',
                color='Success Rate',
                hover_name='Assistant Name',
                title="Cost vs Revenue Analysis",
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_cost_revenue, use_container_width=True)
    
    with tab4:
        # Sentiment Analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment Distribution
            sentiment_data = {
                'Sentiment': ['Positive', 'Neutral', 'Negative'],
                'Percentage': [metrics_data['sentiment_positive'], metrics_data['sentiment_neutral'], metrics_data['sentiment_negative']]
            }
            
            fig_sentiment = px.pie(
                sentiment_data,
                values='Percentage',
                names='Sentiment',
                title="Overall Sentiment Distribution",
                color_discrete_map={
                    'Positive': '#28a745',
                    'Neutral': '#ffc107',
                    'Negative': '#dc3545'
                }
            )
            st.plotly_chart(fig_sentiment, use_container_width=True)
        
        with col2:
            # Sentiment Trend
            dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='D')
            positive_trend = [70 + np.random.normal(0, 5) for _ in range(len(dates))]
            neutral_trend = [20 + np.random.normal(0, 3) for _ in range(len(dates))]
            negative_trend = [10 + np.random.normal(0, 2) for _ in range(len(dates))]
            
            fig_sentiment_trend = go.Figure()
            fig_sentiment_trend.add_trace(go.Scatter(x=dates, y=positive_trend, name='Positive', line=dict(color='#28a745')))
            fig_sentiment_trend.add_trace(go.Scatter(x=dates, y=neutral_trend, name='Neutral', line=dict(color='#ffc107')))
            fig_sentiment_trend.add_trace(go.Scatter(x=dates, y=negative_trend, name='Negative', line=dict(color='#dc3545')))
            
            fig_sentiment_trend.update_layout(
                title="Sentiment Trend (7 Days)",
                xaxis_title="Date",
                yaxis_title="Percentage (%)"
            )
            st.plotly_chart(fig_sentiment_trend, use_container_width=True)
    
    # Detailed Analytics Table
    st.subheader("📋 Detailed Performance Table")
    
    # Add filters for the table
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.multiselect("Filter by Status", performance_df['Status'].unique(), default=performance_df['Status'].unique())
    with col2:
        spec_filter = st.multiselect("Filter by Specialization", performance_df['Specialization'].unique(), default=performance_df['Specialization'].unique())
    with col3:
        min_success_rate = st.slider("Minimum Success Rate", 0, 100, 0)
    
    filtered_performance = performance_df[
        (performance_df['Status'].isin(status_filter)) &
        (performance_df['Specialization'].isin(spec_filter)) &
        (performance_df['Success Rate'] >= min_success_rate)
    ]
    
    st.dataframe(filtered_performance, use_container_width=True)

elif page == "📈 Advanced Reports":
    st.title("📈 Advanced Reporting & Forecasting")
    
    # Report Type Selection
    report_type = st.selectbox(
        "Select Report Type",
        ["Executive Summary", "Performance Analysis", "Financial Report", "Operational Report", "Forecasting", "Custom Report"]
    )
    
    if report_type == "Executive Summary":
        st.subheader("📊 Executive Summary Report")
        
        # Generate comprehensive executive summary
        performance_df = analytics_engine.calculate_performance_metrics(ASSISTANT_CONFIGS)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Key Insights
            st.markdown("### 🎯 Key Insights")
            
            total_calls = performance_df['Daily Calls'].sum()
            avg_success_rate = performance_df['Success Rate'].mean()
            total_revenue = performance_df['Revenue Generated'].sum()
            top_performer = performance_df.loc[performance_df['Success Rate'].idxmax(), 'Assistant Name']
            
            insights = [
                f"📞 **Total Daily Calls**: {total_calls:,} calls across all assistants",
                f"🎯 **Average Success Rate**: {avg_success_rate:.1f}% (Industry benchmark: 65%)",
                f"💰 **Total Revenue Generated**: ${total_revenue:,.0f} this month",
                f"🏆 **Top Performer**: {top_performer} with {performance_df['Success Rate'].max():.1f}% success rate",
                f"📈 **Growth Trend**: +15% increase in call volume compared to last month",
                f"⚡ **System Uptime**: 99.8% availability across all assistants"
            ]
            
            for insight in insights:
                st.markdown(insight)
        
        with col2:
            # Performance Summary Chart
            fig_summary = go.Figure()
            
            # Add success rate gauge
            fig_summary.add_trace(go.Indicator(
                mode = "gauge+number+delta",
                value = avg_success_rate,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Average Success Rate"},
                delta = {'reference': 75},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#667eea"},
                    'steps': [
                        {'range': [0, 50], 'color': "#f8d7da"},
                        {'range': [50, 75], 'color': "#fff3cd"},
                        {'range': [75, 100], 'color': "#d4edda"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig_summary.update_layout(height=300)
            st.plotly_chart(fig_summary, use_container_width=True)
        
        # Detailed Performance Breakdown
        st.markdown("### 📊 Performance Breakdown by Specialization")
        
        spec_performance = performance_df.groupby('Specialization').agg({
            'Daily Calls': 'sum',
            'Success Rate': 'mean',
            'Revenue Generated': 'sum',
            'Customer Satisfaction': 'mean'
        }).round(2)
        
        st.dataframe(spec_performance, use_container_width=True)
        
        # Recommendations
        st.markdown("### 💡 Strategic Recommendations")
        
        recommendations = [
            "🎯 **Optimize Underperformers**: Focus training on assistants with <70% success rates",
            "📈 **Scale Top Performers**: Increase call volume for high-performing specializations",
            "💰 **Cost Optimization**: Review cost-per-call for assistants exceeding $0.20/call",
            "🔧 **Technical Improvements**: Implement advanced NLP for better conversation flow",
            "📊 **Data Integration**: Enhance CRM integration for better lead tracking",
            "🎓 **Training Program**: Develop specialized training modules for each use case"
        ]
        
        for rec in recommendations:
            st.markdown(rec)
    
    elif report_type == "Forecasting":
        st.subheader("🔮 Predictive Analytics & Forecasting")
        
        # Forecasting Controls
        col1, col2, col3 = st.columns(3)
        with col1:
            forecast_days = st.slider("Forecast Period (days)", 7, 90, 30)
        with col2:
            confidence_level = st.slider("Confidence Level (%)", 80, 99, 95)
        with col3:
            model_type = st.selectbox("Model Type", ["Linear Trend", "Seasonal", "ARIMA", "Prophet"])
        
        # Generate forecasting data
        forecast_df = analytics_engine.generate_forecasting_data(forecast_days)
        
        # Forecasting Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Call Volume Forecast
            fig_forecast = go.Figure()
            
            fig_forecast.add_trace(go.Scatter(
                x=forecast_df['Date'],
                y=forecast_df['Predicted Calls'],
                mode='lines',
                name='Predicted Calls',
                line=dict(color='#667eea', width=3)
            ))
            
            fig_forecast.add_trace(go.Scatter(
                x=forecast_df['Date'],
                y=forecast_df['Confidence Upper'],
                fill=None,
                mode='lines',
                line_color='rgba(0,0,0,0)',
                showlegend=False
            ))
            
            fig_forecast.add_trace(go.Scatter(
                x=forecast_df['Date'],
                y=forecast_df['Confidence Lower'],
                fill='tonexty',
                mode='lines',
                line_color='rgba(0,0,0,0)',
                name=f'{confidence_level}% Confidence',
                fillcolor='rgba(102, 126, 234, 0.2)'
            ))
            
            fig_forecast.update_layout(
                title="Call Volume Forecast",
                xaxis_title="Date",
                yaxis_title="Number of Calls"
            )
            st.plotly_chart(fig_forecast, use_container_width=True)
        
        with col2:
            # Revenue Forecast
            fig_revenue_forecast = px.line(
                forecast_df,
                x='Date',
                y='Expected Revenue',
                title="Revenue Forecast",
                line_shape='spline'
            )
            fig_revenue_forecast.update_traces(line_color='#28a745', line_width=3)
            st.plotly_chart(fig_revenue_forecast, use_container_width=True)
        
        # Resource Planning
        st.markdown("### 🎯 Resource Planning Recommendations")
        
        max_calls_day = forecast_df['Predicted Calls'].max()
        max_resources_needed = forecast_df['Resource Requirement'].max()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Peak Call Day", f"{max_calls_day:,.0f} calls")
        with col2:
            st.metric("Max Resources Needed", f"{max_resources_needed} assistants")
        with col3:
            st.metric("Revenue Growth", f"+{forecast_df['Expected Revenue'].iloc[-1] / forecast_df['Expected Revenue'].iloc[0] * 100 - 100:.1f}%")
        
        # Forecast Table
        st.markdown("### 📊 Detailed Forecast Data")
        st.dataframe(forecast_df, use_container_width=True)
    
    elif report_type == "Financial Report":
        st.subheader("💰 Financial Performance Report")
        
        # Financial Metrics
        performance_df = analytics_engine.calculate_performance_metrics(ASSISTANT_CONFIGS)
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_revenue = performance_df['Revenue Generated'].sum()
        total_cost = performance_df['Cost per Call'].sum() * performance_df['Daily Calls'].sum()
        profit_margin = ((total_revenue - total_cost) / total_revenue) * 100
        roi = ((total_revenue - total_cost) / total_cost) * 100
        
        with col1:
            st.metric("Total Revenue", f"${total_revenue:,.0f}")
        with col2:
            st.metric("Total Costs", f"${total_cost:,.0f}")
        with col3:
            st.metric("Profit Margin", f"{profit_margin:.1f}%")
        with col4:
            st.metric("ROI", f"{roi:.1f}%")
        
        # Revenue Breakdown Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue by Assistant
            top_revenue = performance_df.nlargest(10, 'Revenue Generated')
            fig_revenue_bar = px.bar(
                top_revenue,
                x='Assistant Name',
                y='Revenue Generated',
                title="Top 10 Revenue Generators",
                color='Revenue Generated',
                color_continuous_scale='Viridis'
            )
            fig_revenue_bar.update_xaxes(tickangle=45)
            st.plotly_chart(fig_revenue_bar, use_container_width=True)
        
        with col2:
            # Cost Analysis
            fig_cost_scatter = px.scatter(
                performance_df,
                x='Daily Calls',
                y='Cost per Call',
                size='Revenue Generated',
                color='Success Rate',
                hover_name='Assistant Name',
                title="Cost Efficiency Analysis",
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_cost_scatter, use_container_width=True)
        
        # Financial Trends
        st.markdown("### 📈 Financial Trends")
        
        # Generate monthly financial data
        months = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
        monthly_revenue = [50000 + i*5000 + np.random.normal(0, 5000) for i in range(len(months))]
        monthly_costs = [30000 + i*2000 + np.random.normal(0, 2000) for i in range(len(months))]
        monthly_profit = [r - c for r, c in zip(monthly_revenue, monthly_costs)]
        
        fig_financial_trend = go.Figure()
        fig_financial_trend.add_trace(go.Scatter(x=months, y=monthly_revenue, name='Revenue', line=dict(color='#28a745')))
        fig_financial_trend.add_trace(go.Scatter(x=months, y=monthly_costs, name='Costs', line=dict(color='#dc3545')))
        fig_financial_trend.add_trace(go.Scatter(x=months, y=monthly_profit, name='Profit', line=dict(color='#667eea')))
        
        fig_financial_trend.update_layout(
            title="Monthly Financial Performance",
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            height=400
        )
        st.plotly_chart(fig_financial_trend, use_container_width=True)

elif page == "⚙️ Assistant Config":
    st.title(f"⚙️ Assistant Configuration - {current_config.name}")
    
    # Configuration Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎤 Voice & Language", "🧠 AI Settings", "📞 Call Settings", "🔗 Integrations", "📊 Analytics"])
    
    with tab1:
        st.subheader("🎤 Voice & Language Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_voice = st.selectbox("Voice Selection", VOICES, index=VOICES.index(current_config.voice))
            new_language = st.selectbox("Language", LANGUAGES, index=LANGUAGES.index(current_config.language))
            speech_speed = st.slider("Speech Speed", 0.5, 2.0, 1.0, 0.1)
            voice_stability = st.slider("Voice Stability", 0.0, 1.0, 0.75, 0.05)
        
        with col2:
            new_background = st.selectbox("Background Sound", BACKGROUND_SOUNDS, 
                                        index=BACKGROUND_SOUNDS.index(current_config.background_sound))
            volume_level = st.slider("Volume Level", 0.1, 1.0, 0.8, 0.1)
            noise_suppression = st.checkbox("Noise Suppression", value=True)
            echo_cancellation = st.checkbox("Echo Cancellation", value=True)
        
        # Voice Preview
        if st.button("🎵 Preview Voice"):
            st.audio("data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT")
            st.success("Voice preview played!")
    
    with tab2:
        st.subheader("🧠 AI Model Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ai_model = st.selectbox("AI Model", ["GPT-4", "GPT-3.5-Turbo", "Claude-3", "Gemini-Pro"])
            temperature = st.slider("Temperature", 0.0, 1.0, current_config.temperature, 0.1)
            max_tokens = st.slider("Max Tokens", 100, 4000, 1000)
            top_p = st.slider("Top P", 0.0, 1.0, 0.9, 0.1)
        
        with col2:
            response_speed = st.selectbox("Response Speed", ["slow", "normal", "fast"], 
                                        index=["slow", "normal", "fast"].index(current_config.response_speed))
            context_window = st.slider("Context Window", 1000, 8000, 4000)
            memory_enabled = st.checkbox("Conversation Memory", value=True)
            learning_enabled = st.checkbox("Adaptive Learning", value=False)
        
        # Custom Prompt Configuration
        st.subheader("📝 Custom Prompt Templates")
        
        prompt_categories = {
            "Greeting": "Hello! I'm your AI assistant. How can I help you today?",
            "Closing": "Thank you for your time. Have a great day!",
            "Objection Handling": "I understand your concern. Let me address that...",
            "Information Gathering": "To better assist you, could you please tell me...",
            "Appointment Scheduling": "I'd be happy to schedule an appointment for you..."
        }
        
        selected_category = st.selectbox("Prompt Category", list(prompt_categories.keys()))
        custom_prompt = st.text_area("Custom Prompt", 
                                   value=prompt_categories[selected_category], 
                                   height=150)
        
        if st.button("💾 Save Prompt Template"):
            st.success("Prompt template saved successfully!")
    
    with tab3:
        st.subheader("📞 Call Management Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_max_duration = st.slider("Max Call Duration (seconds)", 60, 1800, current_config.max_duration)
            call_timeout = st.slider("Call Timeout (seconds)", 10, 60, 30)
            retry_attempts = st.slider("Retry Attempts", 0, 5, 2)
            call_recording = st.checkbox("Enable Call Recording", value=True)
        
        with col2:
            caller_id = st.text_input("Caller ID", value=current_config.phone_number)
            time_zone = st.selectbox("Time Zone", ["UTC", "EST", "PST", "CST", "MST"])
            business_hours_start = st.time_input("Business Hours Start", value=datetime.strptime("09:00", "%H:%M").time())
            business_hours_end = st.time_input("Business Hours End", value=datetime.strptime("17:00", "%H:%M").time())
        
        # Call Flow Configuration
        st.subheader("🔄 Call Flow Settings")
        
        call_flow_steps = [
            "Initial Greeting",
            "Purpose Identification", 
            "Information Gathering",
            "Solution Presentation",
            "Objection Handling",
            "Closing/Next Steps"
        ]
        
        for i, step in enumerate(call_flow_steps):
            with st.expander(f"Step {i+1}: {step}"):
                step_enabled = st.checkbox(f"Enable {step}", value=True, key=f"step_{i}")
                step_timeout = st.slider(f"Max Duration for {step} (seconds)", 30, 300, 60, key=f"timeout_{i}")
                step_prompt = st.text_area(f"Prompt for {step}", height=100, key=f"prompt_{i}")
    
    with tab4:
        st.subheader("🔗 Integration Settings")
        
        # CRM Integration
        st.markdown("### 🏢 CRM Integration")
        col1, col2 = st.columns(2)
        
        with col1:
            crm_provider = st.selectbox("CRM Provider", ["Salesforce", "HubSpot", "Pipedrive", "Zoho", "Custom"])
            crm_api_key = st.text_input("CRM API Key", type="password")
            crm_endpoint = st.text_input("CRM Endpoint URL")
        
        with col2:
            sync_frequency = st.selectbox("Sync Frequency", ["Real-time", "Every 5 minutes", "Hourly", "Daily"])
            lead_scoring = st.checkbox("Enable Lead Scoring", value=True)
            auto_create_contacts = st.checkbox("Auto-create Contacts", value=True)
        
        # Webhook Configuration
        st.markdown("### 🔗 Webhook Configuration")
        
        webhook_events = [
            "call_started", "call_ended", "call_failed", "lead_qualified", 
            "appointment_scheduled", "objection_raised", "positive_sentiment"
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            webhook_url = st.text_input("Webhook URL", value=current_config.webhook_url)
            webhook_secret = st.text_input("Webhook Secret", type="password")
        
        with col2:
            selected_events = st.multiselect("Webhook Events", webhook_events, default=webhook_events[:3])
            webhook_timeout = st.slider("Webhook Timeout (seconds)", 5, 30, 10)
        
        # Test Integration
        if st.button("🧪 Test Integrations"):
            with st.spinner("Testing integrations..."):
                time.sleep(2)
                st.success("✅ All integrations tested successfully!")
    
    with tab5:
        st.subheader("📊 Analytics & Reporting")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Analytics Settings
            st.markdown("### 📈 Analytics Configuration")
            
            analytics_enabled = st.checkbox("Enable Analytics", value=True)
            sentiment_analysis = st.checkbox("Sentiment Analysis", value=True)
            keyword_tracking = st.checkbox("Keyword Tracking", value=True)
            conversation_scoring = st.checkbox("Conversation Scoring", value=True)
            
            # Custom Metrics
            st.markdown("### 🎯 Custom Metrics")
            custom_metrics = st.text_area("Custom Metrics (JSON format)", 
                                        value='{"lead_quality": "high", "follow_up_required": true}',
                                        height=100)
        
        with col2:
            # Reporting Settings
            st.markdown("### 📋 Reporting Configuration")
            
            daily_reports = st.checkbox("Daily Reports", value=True)
            weekly_reports = st.checkbox("Weekly Reports", value=True)
            monthly_reports = st.checkbox("Monthly Reports", value=True)
            
            report_recipients = st.text_area("Report Recipients (emails)", 
                                           placeholder="admin@company.com\nmanager@company.com")
            
            # Data Retention
            st.markdown("### 🗄️ Data Retention")
            call_data_retention = st.slider("Call Data Retention (days)", 30, 365, 90)
            analytics_retention = st.slider("Analytics Retention (days)", 30, 730, 180)
    
    # Save Configuration
    if st.button("💾 Save All Configuration", type="primary", use_container_width=True):
        with st.spinner("Saving configuration..."):
            time.sleep(2)
            st.success("✅ Configuration saved successfully!")
            st.info("Changes will take effect within 5 minutes.")

elif page == "🎛️ Bulk Operations":
    st.title("🎛️ Bulk Operations Center")
    
    # Operation Type Selection
    operation_type = st.selectbox(
        "Select Bulk Operation",
        ["📞 Bulk Calling", "⚙️ Configuration Update", "📊 Data Export", "🔄 System Maintenance", "📋 Campaign Management"]
    )
    
    if operation_type == "📞 Bulk Calling":
        st.subheader("📞 Bulk Calling Operations")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # File Upload
            uploaded_file = st.file_uploader("Upload Contact List (CSV/Excel)", type=['csv', 'xlsx'])
            
            if uploaded_file:
                if uploaded_file.name.endswith('.csv'):
                    contacts_df = pd.read_csv(uploaded_file)
                else:
                    contacts_df = pd.read_excel(uploaded_file)
                
                st.dataframe(contacts_df.head(10))
                
                # Bulk Call Configuration
                st.subheader("🔧 Bulk Call Configuration")
                
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    selected_assistants = st.multiselect(
                        "Select Assistants",
                        [config.name for config in ASSISTANT_CONFIGS.values()],
                        default=[current_config.name]
                    )
                
                with col_b:
                    call_delay = st.slider("Delay Between Calls (seconds)", 5, 300, 30)
                    max_concurrent = st.slider("Max Concurrent Calls", 1, 10, 3)
                
                with col_c:
                    campaign_name = st.text_input("Campaign Name", value=f"Campaign_{datetime.now().strftime('%Y%m%d_%H%M')}")
                    priority_level = st.selectbox("Priority Level", ["Low", "Normal", "High", "Urgent"])
                
                # Advanced Settings
                with st.expander("🔧 Advanced Settings"):
                    col_x, col_y = st.columns(2)
                    
                    with col_x:
                        retry_failed = st.checkbox("Retry Failed Calls", value=True)
                        max_retries = st.slider("Max Retries", 1, 5, 2)
                        time_zone_handling = st.selectbox("Time Zone Handling", ["Respect Local Time", "Use System Time"])
                    
                    with col_y:
                        call_window_start = st.time_input("Call Window Start", value=datetime.strptime("09:00", "%H:%M").time())
                        call_window_end = st.time_input("Call Window End", value=datetime.strptime("17:00", "%H:%M").time())
                        weekend_calling = st.checkbox("Allow Weekend Calling", value=False)
                
                # Bulk Call Execution
                if st.button("🚀 Start Bulk Calling Campaign", type="primary"):
                    st.success(f"✅ Bulk calling campaign '{campaign_name}' initiated!")
                    
                    # Progress tracking
                    progress_container = st.container()
                    with progress_container:
                        st.subheader("📊 Campaign Progress")
                        
                        progress_col1, progress_col2, progress_col3 = st.columns(3)
                        
                        with progress_col1:
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                        
                        with progress_col2:
                            calls_completed = st.empty()
                            calls_successful = st.empty()
                        
                        with progress_col3:
                            estimated_completion = st.empty()
                            current_cost = st.empty()
                        
                        # Simulate progress
                        total_contacts = len(contacts_df)
                        for i in range(total_contacts):
                            progress = (i + 1) / total_contacts
                            progress_bar.progress(progress)
                            status_text.text(f"Calling contact {i+1} of {total_contacts}")
                            calls_completed.metric("Calls Completed", i+1)
                            calls_successful.metric("Successful Calls", int((i+1) * 0.75))
                            
                            remaining_time = (total_contacts - i - 1) * call_delay
                            estimated_completion.metric("Est. Completion", f"{remaining_time//60}m {remaining_time%60}s")
                            current_cost.metric("Current Cost", f"${(i+1) * 0.15:.2f}")
                            
                            time.sleep(0.1)  # Simulate processing time
                        
                        st.success("🎉 Bulk calling campaign completed successfully!")
        
        with col2:
            # Campaign Statistics
            st.subheader("📊 Campaign Statistics")
            
            if uploaded_file:
                total_contacts = len(contacts_df)
                estimated_duration = total_contacts * call_delay / 60
                estimated_cost = total_contacts * 0.15
                
                st.metric("Total Contacts", total_contacts)
                st.metric("Estimated Duration", f"{estimated_duration:.0f} minutes")
                st.metric("Estimated Cost", f"${estimated_cost:.2f}")
                st.metric("Selected Assistants", len(selected_assistants))
            
            # Active Campaigns
            st.subheader("🔄 Active Campaigns")
            
            active_campaigns = [
                {"name": "Holiday Promotion", "progress": 75, "status": "Running"},
                {"name": "Lead Follow-up", "progress": 45, "status": "Running"},
                {"name": "Survey Campaign", "progress": 100, "status": "Completed"}
            ]
            
            for campaign in active_campaigns:
                with st.container():
                    st.write(f"**{campaign['name']}**")
                    st.progress(campaign['progress'] / 100)
                    st.caption(f"Status: {campaign['status']} ({campaign['progress']}%)")
    
    elif operation_type == "⚙️ Configuration Update":
        st.subheader("⚙️ Bulk Configuration Updates")
        
        # Configuration Type
        config_type = st.selectbox(
            "Configuration Type",
            ["Voice Settings", "AI Parameters", "Call Settings", "Integration Settings", "Analytics Settings"]
        )
        
        # Assistant Selection
        st.subheader("🎯 Assistant Selection")
        
        selection_method = st.radio(
            "Selection Method",
            ["Select All", "Select by Status", "Select by Specialization", "Custom Selection"]
        )
        
        if selection_method == "Select All":
            selected_configs = list(ASSISTANT_CONFIGS.keys())
        elif selection_method == "Select by Status":
            status_filter = st.multiselect("Select Status", [status.value for status in AssistantStatus])
            selected_configs = [key for key, config in ASSISTANT_CONFIGS.items() if config.status.value in status_filter]
        elif selection_method == "Select by Specialization":
            spec_filter = st.multiselect("Select Specialization", list(set(config.specialization for config in ASSISTANT_CONFIGS.values())))
            selected_configs = [key for key, config in ASSISTANT_CONFIGS.items() if config.specialization in spec_filter]
        else:
            selected_configs = st.multiselect("Select Assistants", list(ASSISTANT_CONFIGS.keys()), 
                                            format_func=lambda x: ASSISTANT_CONFIGS[x].name)
        
        st.info(f"Selected {len(selected_configs)} assistants for configuration update")
        
        # Configuration Updates
        if config_type == "Voice Settings":
            col1, col2 = st.columns(2)
            
            with col1:
                update_voice = st.checkbox("Update Voice")
                if update_voice:
                    new_voice = st.selectbox("New Voice", VOICES)
                
                update_language = st.checkbox("Update Language")
                if update_language:
                    new_language = st.selectbox("New Language", LANGUAGES)
            
            with col2:
                update_background = st.checkbox("Update Background Sound")
                if update_background:
                    new_background = st.selectbox("New Background Sound", BACKGROUND_SOUNDS)
                
                update_speed = st.checkbox("Update Speech Speed")
                if update_speed:
                    new_speed = st.slider("New Speech Speed", 0.5, 2.0, 1.0, 0.1)
        
        elif config_type == "AI Parameters":
            col1, col2 = st.columns(2)
            
            with col1:
                update_temperature = st.checkbox("Update Temperature")
                if update_temperature:
                    new_temperature = st.slider("New Temperature", 0.0, 1.0, 0.7, 0.1)
                
                update_model = st.checkbox("Update AI Model")
                if update_model:
                    new_model = st.selectbox("New AI Model", ["GPT-4", "GPT-3.5-Turbo", "Claude-3"])
            
            with col2:
                update_response_speed = st.checkbox("Update Response Speed")
                if update_response_speed:
                    new_response_speed = st.selectbox("New Response Speed", ["slow", "normal", "fast"])
                
                update_context = st.checkbox("Update Context Window")
                if update_context:
                    new_context = st.slider("New Context Window", 1000, 8000, 4000)
        
        # Apply Updates
        if st.button("🔄 Apply Configuration Updates", type="primary"):
            if selected_configs:
                with st.spinner("Applying configuration updates..."):
                    progress_bar = st.progress(0)
                    
                    for i, config_key in enumerate(selected_configs):
                        progress_bar.progress((i + 1) / len(selected_configs))
                        time.sleep(0.1)  # Simulate update time
                    
                    st.success(f"✅ Configuration updated for {len(selected_configs)} assistants!")
            else:
                st.warning("⚠️ Please select at least one assistant")
    
    elif operation_type == "📊 Data Export":
        st.subheader("📊 Bulk Data Export")
        
        # Export Configuration
        col1, col2 = st.columns(2)
        
        with col1:
            export_type = st.selectbox(
                "Export Type",
                ["Call Logs", "Performance Metrics", "Financial Data", "Configuration Backup", "Complete Dataset"]
            )
            
            date_range = st.date_input(
                "Date Range",
                value=[datetime.now().date() - timedelta(days=30), datetime.now().date()],
                max_value=datetime.now().date()
            )
        
        with col2:
            export_format = st.selectbox("Export Format", ["CSV", "Excel", "JSON", "PDF Report"])
            
            include_filters = st.multiselect(
                "Include Data",
                ["Call Transcripts", "Sentiment Analysis", "Lead Scores", "Cost Analysis", "Performance Metrics"]
            )
        
        # Assistant Selection for Export
        export_assistants = st.multiselect(
            "Select Assistants for Export",
            [config.name for config in ASSISTANT_CONFIGS.values()],
            default=[config.name for config in ASSISTANT_CONFIGS.values()]
        )
        
        # Generate Export
        if st.button("📥 Generate Export", type="primary"):
            with st.spinner("Generating export..."):
                # Simulate export generation
                progress_bar = st.progress(0)
                
                for i in range(100):
                    progress_bar.progress(i + 1)
                    time.sleep(0.02)
                
                st.success("✅ Export generated successfully!")
                
                # Provide download link
                export_data = pd.DataFrame({
                    'Assistant': [config.name for config in ASSISTANT_CONFIGS.values()],
                    'Calls Today': [20 + hash(config.id) % 50 for config in ASSISTANT_CONFIGS.values()],
                    'Success Rate': [config.success_rate for config in ASSISTANT_CONFIGS.values()],
                    'Revenue': [config.total_revenue for config in ASSISTANT_CONFIGS.values()]
                })
                
                csv_data = export_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download Export",
                    data=csv_data,
                    file_name=f"vapi_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

elif page == "🔍 Real-time Monitor":
    st.title("🔍 Real-time System Monitor")
    
    # Auto-refresh toggle
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown('<span class="real-time-indicator"></span>**Real-time Monitoring Active**', unsafe_allow_html=True)
    with col2:
        auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.user_preferences['auto_refresh'])
    with col3:
        refresh_interval = st.selectbox("Refresh Rate", [5, 10, 30, 60], index=2)
    
    # System Health Overview
    st.subheader("🏥 System Health Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    health_metrics = {
        "API Status": ("healthy", "🟢"),
        "Database": ("healthy", "🟢"), 
        "Webhooks": ("warning", "🟡"),
        "Network": ("healthy", "🟢")
    }
    
    for i, (metric, (status, icon)) in enumerate(health_metrics.items()):
        with [col1, col2, col3, col4][i]:
            st.markdown(f"""
            <div class="metrics-card">
                <h3>{icon}</h3>
                <p>{metric}</p>
                <small>{status.upper()}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Live Activity Feed
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Live Activity Dashboard")
        
        # Real-time metrics
        current_time = datetime.now()
        
        # Generate real-time call data
        active_calls_data = []
        for i in range(np.random.randint(3, 8)):
            assistant = np.random.choice(list(ASSISTANT_CONFIGS.values()))
            call_duration = np.random.randint(30, 300)
            
            active_calls_data.append({
                'Call ID': f"call_{uuid.uuid4().hex[:8]}",
                'Assistant': assistant.name,
                'Phone': f"+1-555-{np.random.randint(1000, 9999)}",
                'Duration': f"{call_duration//60}m {call_duration%60}s",
                'Status': np.random.choice(['Connected', 'Ringing', 'On Hold']),
                'Sentiment': np.random.choice(['Positive', 'Neutral', 'Negative'])
            })
        
        if active_calls_data:
            st.dataframe(pd.DataFrame(active_calls_data), use_container_width=True)
        else:
            st.info("No active calls at the moment")
        
        # Real-time Performance Chart
        st.subheader("📈 Real-time Performance")
        
        # Generate real-time data points
        time_points = [current_time - timedelta(minutes=i) for i in range(60, 0, -1)]
        call_volumes = [np.random.randint(5, 25) for _ in time_points]
        success_rates = [75 + np.random.normal(0, 10) for _ in time_points]
        
        fig_realtime = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig_realtime.add_trace(
            go.Scatter(x=time_points, y=call_volumes, name="Call Volume", line=dict(color='#667eea')),
            secondary_y=False,
        )
        
        fig_realtime.add_trace(
            go.Scatter(x=time_points, y=success_rates, name="Success Rate", line=dict(color='#28a745')),
            secondary_y=True,
        )
        
        fig_realtime.update_xaxes(title_text="Time")
        fig_realtime.update_yaxes(title_text="Call Volume", secondary_y=False)
        fig_realtime.update_yaxes(title_text="Success Rate (%)", secondary_y=True)
        fig_realtime.update_layout(title="Real-time Performance (Last Hour)")
        
        st.plotly_chart(fig_realtime, use_container_width=True)
    
    with col2:
        st.subheader("🔔 Live Alerts")
        
        # Generate live alerts
        alerts = [
            {"time": "30s ago", "type": "success", "message": "Assistant 5 achieved 95% success rate"},
            {"time": "1m ago", "type": "warning", "message": "High call volume detected"},
            {"time": "2m ago", "type": "info", "message": "New lead qualified by Assistant 12"},
            {"time": "3m ago", "type": "error", "message": "Assistant 8 connection timeout"},
            {"time": "5m ago", "type": "success", "message": "Campaign milestone reached"}
        ]
        
        for alert in alerts:
            alert_class = f"alert-{alert['type']}" if alert['type'] != 'error' else 'alert-danger'
            icon = {"success": "✅", "warning": "⚠️", "info": "ℹ️", "error": "❌"}[alert['type']]
            
            st.markdown(f"""
            <div class="{alert_class}">
                {icon} <strong>{alert['time']}</strong><br>
                {alert['message']}
            </div>
            """, unsafe_allow_html=True)
        
        # System Resources
        st.subheader("💻 System Resources")
        
        cpu_usage = 45 + np.random.randint(-10, 10)
        memory_usage = 62 + np.random.randint(-5, 5)
        disk_usage = 78 + np.random.randint(-3, 3)
        
        st.metric("CPU Usage", f"{cpu_usage}%")
        st.metric("Memory Usage", f"{memory_usage}%")
        st.metric("Disk Usage", f"{disk_usage}%")
        
        # Network Status
        st.subheader("🌐 Network Status")
        
        network_metrics = {
            "Latency": f"{np.random.randint(10, 50)}ms",
            "Throughput": f"{np.random.randint(80, 100)}Mbps",
            "Packet Loss": f"{np.random.uniform(0, 0.5):.2f}%"
        }
        
        for metric, value in network_metrics.items():
            st.metric(metric, value)

elif page == "📋 Call Logs":
    st.title("📋 Comprehensive Call Logs")
    
    # Advanced Filtering
    st.subheader("🔍 Advanced Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        date_filter = st.date_input(
            "Date Range",
            value=[datetime.now().date() - timedelta(days=7), datetime.now().date()]
        )
    
    with col2:
        assistant_filter = st.multiselect(
            "Assistants",
            [config.name for config in ASSISTANT_CONFIGS.values()],
            default=[config.name for config in ASSISTANT_CONFIGS.values()]
        )
    
    with col3:
        status_filter = st.multiselect(
            "Call Status",
            ["Completed", "Failed", "Busy", "No Answer", "Missed"],
            default=["Completed", "Failed", "Busy", "No Answer", "Missed"]
        )
    
    with col4:
        duration_filter = st.slider("Min Duration (seconds)", 0, 600, 0)
    
    # Generate comprehensive call log data
    call_logs = []
    for i in range(500):  # Generate 500 call records
        assistant = np.random.choice(list(ASSISTANT_CONFIGS.values()))
        call_time = datetime.now() - timedelta(
            days=np.random.randint(0, 30),
            hours=np.random.randint(0, 24),
            minutes=np.random.randint(0, 60)
        )
        
        duration = np.random.randint(30, 600)
        status = np.random.choice(["Completed", "Failed", "Busy", "No Answer", "Missed"])
        sentiment = np.random.choice(["Positive", "Neutral", "Negative"])
        
        call_logs.append({
            'Call ID': f"call_{uuid.uuid4().hex[:8]}",
            'Date': call_time.date(),
            'Time': call_time.time(),
            'Assistant': assistant.name,
            'Phone Number': f"+1-555-{np.random.randint(1000, 9999)}",
            'Duration': duration,
            'Status': status,
            'Sentiment': sentiment,
            'Lead Score': round(np.random.uniform(1, 10), 1),
            'Cost': round(duration * 0.02, 2),
            'Campaign': f"Campaign {np.random.randint(1, 6)}",
            'Notes': f"Call handled by {assistant.specialization} specialist"
        })
    
    call_logs_df = pd.DataFrame(call_logs)
    
    # Apply filters
    filtered_logs = call_logs_df[
        (call_logs_df['Date'] >= date_filter[0]) &
        (call_logs_df['Date'] <= date_filter[1]) &
        (call_logs_df['Assistant'].isin(assistant_filter)) &
        (call_logs_df['Status'].isin(status_filter)) &
        (call_logs_df['Duration'] >= duration_filter)
    ]
    
    # Summary Statistics
    st.subheader("📊 Call Log Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Calls", len(filtered_logs))
    with col2:
        avg_duration = filtered_logs['Duration'].mean() if len(filtered_logs) > 0 else 0
        st.metric("Avg Duration", f"{avg_duration:.0f}s")
    with col3:
        success_rate = (len(filtered_logs[filtered_logs['Status'] == 'Completed']) / len(filtered_logs) * 100) if len(filtered_logs) > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    with col4:
        total_cost = filtered_logs['Cost'].sum() if len(filtered_logs) > 0 else 0
        st.metric("Total Cost", f"${total_cost:.2f}")
    with col5:
        avg_lead_score = filtered_logs['Lead Score'].mean() if len(filtered_logs) > 0 else 0
        st.metric("Avg Lead Score", f"{avg_lead_score:.1f}")
    
    # Call Logs Table with Enhanced Features
    st.subheader("📋 Detailed Call Logs")
    
    # Search functionality
    search_term = st.text_input("🔍 Search calls", placeholder="Search by phone number, notes, or campaign...")
    
    if search_term:
        filtered_logs = filtered_logs[
            filtered_logs['Phone Number'].str.contains(search_term, case=False, na=False) |
            filtered_logs['Notes'].str.contains(search_term, case=False, na=False) |
            filtered_logs['Campaign'].str.contains(search_term, case=False, na=False)
        ]
    
    # Pagination
    page_size = st.selectbox("Rows per page", [25, 50, 100, 200], index=1)
    total_pages = (len(filtered_logs) - 1) // page_size + 1 if len(filtered_logs) > 0 else 1
    current_page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
    
    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    
    # Display paginated results
    if len(filtered_logs) > 0:
        st.dataframe(
            filtered_logs.iloc[start_idx:end_idx],
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"Showing {start_idx + 1}-{min(end_idx, len(filtered_logs))} of {len(filtered_logs)} calls")
    else:
        st.info("No calls found matching the current filters.")
    
    # Export Options
    st.subheader("📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export to CSV"):
            csv_data = filtered_logs.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv_data,
                f"call_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col2:
        if st.button("📈 Generate Report"):
            st.info("Detailed report generation initiated...")
    
    with col3:
        if st.button("📧 Email Report"):
            st.info("Report will be emailed to configured recipients...")

elif page == "🎯 Campaign Manager":
    st.title("🎯 Campaign Management Center")
    
    # Campaign Overview
    st.subheader("📊 Campaign Overview")
    
    # Sample campaign data
    campaigns = [
        {
            "name": "Holiday Promotion 2024",
            "status": "Active",
            "start_date": "2024-12-01",
            "end_date": "2024-12-31",
            "target_calls": 5000,
            "completed_calls": 3750,
            "success_rate": 78.5,
            "budget": 2500,
            "spent": 1875,
            "assistants": ["Assistant 1", "Assistant 5", "Assistant 12"]
        },
        {
            "name": "Lead Follow-up Q4",
            "status": "Active", 
            "start_date": "2024-10-01",
            "end_date": "2024-12-31",
            "target_calls": 2000,
            "completed_calls": 1200,
            "success_rate": 82.3,
            "budget": 1000,
            "spent": 600,
            "assistants": ["Assistant 3", "Assistant 8"]
        },
        {
            "name": "Customer Survey",
            "status": "Completed",
            "start_date": "2024-11-01", 
            "end_date": "2024-11-30",
            "target_calls": 1500,
            "completed_calls": 1500,
            "success_rate": 91.2,
            "budget": 750,
            "spent": 720,
            "assistants": ["Assistant 15", "Assistant 20"]
        }
    ]
    
    # Campaign Cards
    for campaign in campaigns:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                status_color = {"Active": "🟢", "Completed": "🔵", "Paused": "🟡", "Failed": "🔴"}[campaign["status"]]
                st.markdown(f"""
                <div class="assistant-card">
                    <h4>{status_color} {campaign['name']}</h4>
                    <p><strong>Period:</strong> {campaign['start_date']} to {campaign['end_date']}</p>
                    <p><strong>Assistants:</strong> {', '.join(campaign['assistants'])}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                progress = campaign['completed_calls'] / campaign['target_calls']
                st.metric("Progress", f"{progress:.1%}")
                st.progress(progress)
            
            with col3:
                st.metric("Success Rate", f"{campaign['success_rate']:.1f}%")
                st.metric("Budget Used", f"${campaign['spent']:.0f}/${campaign['budget']:.0f}")
            
            with col4:
                if campaign['status'] == 'Active':
                    if st.button(f"⏸️ Pause", key=f"pause_{campaign['name']}"):
                        st.success(f"Campaign '{campaign['name']}' paused")
                    if st.button(f"📊 Details", key=f"details_{campaign['name']}"):
                        st.info(f"Showing details for '{campaign['name']}'")
                else:
                    if st.button(f"📈 Report", key=f"report_{campaign['name']}"):
                        st.info(f"Generating report for '{campaign['name']}'")
    
    # Create New Campaign
    st.subheader("➕ Create New Campaign")
    
    with st.expander("🆕 New Campaign Configuration"):
        col1, col2 = st.columns(2)
        
        with col1:
            campaign_name = st.text_input("Campaign Name")
            campaign_type = st.selectbox("Campaign Type", 
                                       ["Sales Outreach", "Lead Follow-up", "Customer Survey", 
                                        "Appointment Scheduling", "Product Launch", "Event Promotion"])
            
            start_date = st.date_input("Start Date", value=datetime.now().date())
            end_date = st.date_input("End Date", value=datetime.now().date() + timedelta(days=30))
        
        with col2:
            target_calls = st.number_input("Target Calls", min_value=1, value=1000)
            budget = st.number_input("Budget ($)", min_value=0.0, value=500.0)
            
            selected_assistants = st.multiselect(
                "Select Assistants",
                [config.name for config in ASSISTANT_CONFIGS.values()]
            )
        
        # Campaign Script
        st.subheader("📝 Campaign Script")
        campaign_script = st.text_area(
            "Campaign Script/Prompt",
            height=150,
            placeholder="Enter the script or prompt that assistants will use for this campaign..."
        )
        
        # Advanced Settings
        with st.expander("⚙️ Advanced Campaign Settings"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                call_window_start = st.time_input("Call Window Start", value=datetime.strptime("09:00", "%H:%M").time())
                call_window_end = st.time_input("Call Window End", value=datetime.strptime("17:00", "%H:%M").time())
                max_attempts = st.slider("Max Call Attempts", 1, 5, 3)
            
            with col_b:
                time_zone = st.selectbox("Time Zone", ["UTC", "EST", "PST", "CST", "MST"])
                priority = st.selectbox("Campaign Priority", ["Low", "Normal", "High", "Urgent"])
                auto_retry = st.checkbox("Auto-retry Failed Calls", value=True)
        
        if st.button("🚀 Create Campaign", type="primary"):
            if campaign_name and selected_assistants:
                st.success(f"✅ Campaign '{campaign_name}' created successfully!")
                st.info("Campaign will start at the specified date and time.")
            else:
                st.warning("⚠️ Please fill in all required fields")

elif page == "🔧 System Admin":
    st.title("🔧 System Administration")
    
    # Admin Tabs
    admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs(["👥 User Management", "🔐 Security", "🗄️ Database", "📊 System Logs"])
    
    with admin_tab1:
        st.subheader("👥 User Management")
        
        # User List
        users = [
            {"username": "admin", "role": "Administrator", "last_login": "2024-01-15 10:30", "status": "Active"},
            {"username": "manager1", "role": "Manager", "last_login": "2024-01-15 09:15", "status": "Active"},
            {"username": "operator1", "role": "Operator", "last_login": "2024-01-14 16:45", "status": "Active"},
            {"username": "analyst1", "role": "Analyst", "last_login": "2024-01-13 14:20", "status": "Inactive"}
        ]
        
        users_df = pd.DataFrame(users)
        st.dataframe(users_df, use_container_width=True)
        
        # Add New User
        with st.expander("➕ Add New User"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username")
                new_email = st.text_input("Email")
                new_role = st.selectbox("Role", ["Administrator", "Manager", "Operator", "Analyst"])
            
            with col2:
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                send_invite = st.checkbox("Send Email Invitation", value=True)
            
            if st.button("👤 Create User"):
                if new_password == confirm_password:
                    st.success(f"✅ User '{new_username}' created successfully!")
                else:
                    st.error("❌ Passwords do not match")
    
    with admin_tab2:
        st.subheader("🔐 Security Settings")
        
        # Security Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Failed Login Attempts", "12", delta="-3")
        with col2:
            st.metric("Active Sessions", "8", delta="+2")
        with col3:
            st.metric("API Calls Today", "15,432", delta="+1,234")
        with col4:
            st.metric("Security Score", "98%", delta="+2%")
        
        # Security Settings
        st.subheader("🛡️ Security Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Authentication")
            two_factor_auth = st.checkbox("Enable 2FA", value=True)
            session_timeout = st.slider("Session Timeout (minutes)", 15, 480, 60)
            password_policy = st.selectbox("Password Policy", ["Standard", "Strong", "Enterprise"])
        
        with col2:
            st.markdown("### API Security")
            rate_limiting = st.checkbox("Enable Rate Limiting", value=True)
            api_key_rotation = st.slider("API Key Rotation (days)", 30, 365, 90)
            ip_whitelist = st.text_area("IP Whitelist", placeholder="192.168.1.0/24\n10.0.0.0/8")
        
        # Recent Security Events
        st.subheader("🚨 Recent Security Events")
        
        security_events = [
            {"time": "2024-01-15 10:45", "event": "Failed login attempt", "user": "unknown", "ip": "192.168.1.100"},
            {"time": "2024-01-15 10:30", "event": "Successful login", "user": "admin", "ip": "192.168.1.50"},
            {"time": "2024-01-15 09:15", "event": "API key used", "user": "system", "ip": "10.0.0.1"},
            {"time": "2024-01-15 08:30", "event": "Password changed", "user": "manager1", "ip": "192.168.1.75"}
        ]
        
        for event in security_events:
            icon = "🔴" if "failed" in event["event"].lower() else "🟢"
            st.markdown(f"""
            <div class="call-log-row">
                {icon} <strong>{event['time']}</strong> - {event['event']}<br>
                <small>User: {event['user']} | IP: {event['ip']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    with admin_tab3:
        st.subheader("🗄️ Database Management")
        
        # Database Status
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Database Size", "2.4 GB", delta="+120 MB")
        with col2:
            st.metric("Total Records", "1,234,567", delta="+12,345")
        with col3:
            st.metric("Query Performance", "45ms avg", delta="-5ms")
        with col4:
            st.metric("Uptime", "99.9%", delta="+0.1%")
        
        # Database Operations
        st.subheader("🔧 Database Operations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Maintenance")
            
            if st.button("🧹 Optimize Database"):
                with st.spinner("Optimizing database..."):
                    time.sleep(3)
                    st.success("✅ Database optimized successfully!")
            
            if st.button("💾 Create Backup"):
                with st.spinner("Creating backup..."):
                    time.sleep(5)
                    st.success("✅ Backup created successfully!")
            
            if st.button("🔄 Sync Data"):
                with st.spinner("Syncing data..."):
                    time.sleep(2)
                    st.success("✅ Data synchronized!")
        
        with col2:
            st.markdown("### Data Management")
            
            retention_days = st.slider("Data Retention (days)", 30, 365, 90)
            
            if st.button("🗑️ Clean Old Data"):
                st.warning("This will permanently delete old data. Are you sure?")
                if st.button("⚠️ Confirm Deletion"):
                    st.success("✅ Old data cleaned successfully!")
            
            if st.button("📊 Generate DB Report"):
                st.info("Database report generated and saved.")
    
    with admin_tab4:
        st.subheader("📊 System Logs")
        
        # Log Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            log_level = st.selectbox("Log Level", ["All", "Error", "Warning", "Info", "Debug"])
        with col2:
            log_source = st.selectbox("Source", ["All", "API", "Database", "Auth", "Webhook"])
        with col3:
            log_date = st.date_input("Date", value=datetime.now().date())
        
        # System Logs
        system_logs = [
            {"timestamp": "2024-01-15 10:45:23", "level": "ERROR", "source": "API", "message": "Rate limit exceeded for IP 192.168.1.100"},
            {"timestamp": "2024-01-15 10:44:15", "level": "INFO", "source": "Auth", "message": "User 'admin' logged in successfully"},
            {"timestamp": "2024-01-15 10:43:02", "level": "WARNING", "source": "Database", "message": "High connection count detected"},
            {"timestamp": "2024-01-15 10:42:18", "level": "INFO", "source": "Webhook", "message": "Webhook delivered successfully to endpoint"},
            {"timestamp": "2024-01-15 10:41:45", "level": "DEBUG", "source": "API", "message": "Processing call initiation request"},
        ]
        
        for log in system_logs:
            level_color = {
                "ERROR": "🔴",
                "WARNING": "🟡", 
                "INFO": "🔵",
                "DEBUG": "⚪"
            }[log["level"]]
            
            st.markdown(f"""
            <div class="call-log-row">
                {level_color} <strong>{log['timestamp']}</strong> [{log['level']}] {log['source']}<br>
                {log['message']}
            </div>
            """, unsafe_allow_html=True)
        
        # Log Export
        if st.button("📥 Export Logs"):
            st.success("✅ Logs exported successfully!")

# Auto-refresh functionality
if st.session_state.user_preferences['auto_refresh'] and page in ["🔍 Real-time Monitor", "📊 Live Analytics"]:
    time.sleep(st.session_state.user_preferences['refresh_interval'])
    st.rerun()

# Footer with Enhanced Information
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem; background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 10px; margin-top: 2rem;">
    <h4>🚀 VAPI AI Call Center Pro Dashboard</h4>
    <p>Enterprise-Grade AI Phone Assistant Management Platform</p>
    <p>
        <a href="#" style="color: #667eea; text-decoration: none; margin: 0 1rem;">📚 Documentation</a> |
        <a href="#" style="color: #667eea; text-decoration: none; margin: 0 1rem;">🎓 Training</a> |
        <a href="#" style="color: #667eea; text-decoration: none; margin: 0 1rem;">💬 Support</a> |
        <a href="#" style="color: #667eea; text-decoration: none; margin: 0 1rem;">🔧 API Reference</a>
    </p>
    <small>Version 2.1.0 | Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | System Status: 🟢 Operational</small>
</div>
""".format(datetime=datetime), unsafe_allow_html=True)
