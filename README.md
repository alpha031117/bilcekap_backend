# Bilcekap Backend Setup

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Database Configuration
DATABASE_URL=sqlite:///./bilcekap.db

# LHDN API Configuration
LHDN_API_URL=https://api.ldhn.gov.my
LHDN_API_KEY=your_ldhn_api_key_here
LHDN_API_TIMEOUT=30

# Security
SECRET_KEY=your_secret_key_here
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Taxpayer Validation
- **URL**: `/api/v1.0/taxpayer/validate/{tin}?idType={idType}&idValue={idValue}`
- **Method**: GET
- **Description**: Validates taxpayer TIN using LHDN API

### Example Request:
```bash
GET /api/v1.0/taxpayer/validate/ABC123456?idType=NRIC&idValue=123456789
```

### Example Response:
```json
{
  "tin": "ABC123456",
  "id_type": "NRIC",
  "id_value": "123456789",
  "is_valid": true,
  "validation_message": "Taxpayer validated successfully",
  "validated_at": "2024-01-15T10:30:00Z"
}
```

## Configuration

The application integrates with the LHDN API to validate taxpayer information. Make sure to:

1. Get the correct LHDN API URL
2. Obtain API key if required
3. Configure the timeout settings appropriately

## Error Handling

The API handles various error scenarios:
- Invalid TIN format
- Invalid ID type or value
- LHDN API unavailable
- Network timeouts
- Authentication failures


