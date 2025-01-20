# Changelog

## [1.0.0] - 2025-01-20
### Phase 1: Core Functions - Completed
- Added journey stage definitions (FIRST_PURCHASE, SIZE_EXPLORATION, etc.)
- Implemented confidence score calculation based on:
  - Size consistency (40%)
  - Return rate (30%)
  - Purchase frequency (30%)
- Added JourneyMapper class with core functionality:
  - Entry point identification
  - Journey stage determination
  - Confidence progression tracking
- Improved data preparation:
  - Size extraction from SKUs
  - Style extraction from product names
  - Proper column handling
- Added comprehensive test suite with 90% coverage
- Fixed all test failures and edge cases

### Added
- Core journey mapping functionality
- Data preparation utilities
- Test suite with fixtures
- Debug logging

### Changed
- Improved size extraction logic
- Enhanced journey stage determination
- Refined confidence score calculation

### Technical Details
- Added type hints for better code clarity
- Implemented proper error handling
- Added detailed logging for debugging
- Created synthetic test data fixtures

## Next Steps
Phase 2: Advanced Features
- Implement advanced pattern matching
- Add visualization capabilities
- Create API endpoints
- Enhance data quality checks