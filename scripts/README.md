# Scripts Directory

This directory contains utility scripts developed for eSports data analysis and visualization during 2022-2023. These scripts were designed to automate data collection, processing, and distribution for team analysis.

## 📊 Data Distribution Scripts

### `send_to_cloud.py`
**Primary data distribution system for team analysis**

Comprehensive script that aggregates and sends match data to Google Sheets for visualization and analysis.

**Features:**
- Pulls data from PostgreSQL databases (official games and scrims)
- Integrates multiple data sources: match stats, drafts, player builds, positioning data
- Creates visual maps showing player positions during objectives
- Includes Leaguepedia integration for historical player data
- Optional SoloQ data integration
- Automated hyperlink creation for multi.op.gg and lolpros profiles

**Data Sheets Created:**
- `draftData` - Pick/ban phase analysis
- `teamData` - Team-level statistics
- `playerData` - Individual player performance
- `buildData` - Items and runes analysis
- `mapInfo` - Visual positioning maps with metadata
- `leaguepediaGames` - Historical tournament data
- `soloqData` - Solo queue performance (optional)

**Usage:** Processes data for teams defined in `config.py` (both `team_info` and `other_team_info`)

### `send_rofl_sheet.py`
**Replay file distribution system**

Specialized script for distributing .rofl replay files to teams for easy game review access.

**Features:**
- Extracts replay download links from database
- Organizes drafts with role-based champion positioning
- Creates accessible format for coaches and players
- Filters and sorts by date for recent games priority

**Output:** Single Google Sheet with downloadable replay links and draft summaries

## 🗺️ Visualization Scripts

### `maps.py`
**Advanced positioning visualization system**

Creates detailed visual maps showing player positions during key game moments.

**Key Features:**
- **Real-time positioning**: Player locations during objectives (lvl1, dragons, barons, heralds)
- **Champion icons**: Dynamic champion portraits with team color borders
- **Death states**: Visual indicators for eliminated players
- **Level 1 analysis**: Special visualization for early game positioning
- **Range indicators**: Colored overlays showing team positioning zones
- **Automated uploads**: Direct S3 integration for cloud storage
- **Multi-threaded processing**: Efficient bulk image generation

**Technical Details:**
- Uses Riot's Data Dragon API for champion images
- PIL (Python Imaging Library) for image manipulation
- Custom masking and overlay systems
- Automatic patch version detection and updates

**Map Elements:**
- 512x512px Summoner's Rift overlay
- 30px champion icons with team-colored borders
- Transparency effects for eliminated players
- Timestamp and objective labeling
- Gold expenditure context

⚠️ **Note**: Original maps hosted on S3 are no longer available due to discontinued bucket usage.

## 📈 Data Collection Scripts

### `playerLeaguepedia.py`
**Tournament data integration**

Interfaces with Leaguepedia's Cargo API to fetch official tournament statistics.

**Methods:**
- `players(teamName)` - Retrieves player roster for specified team
- `player_stats(players)` - Fetches comprehensive match history and performance

**Data Retrieved:**
- Champion picks and win rates
- Match results and dates
- Patch version tracking
- Performance across different tournaments

### `roles.py`
**Player role mapping system**

Automated script for maintaining player role database from Leaguepedia.

**Features:**
- Scrapes European league player information
- Maintains role assignments (Top, Jungle, Mid, Bot, Support)
- Creates comprehensive player database
- Filters active players only
- Exports to CSV for database integration

**Output:** `player_roles.csv` with player metadata

## 🔧 Utility Scripts

### `file_name_url.py`
**MediaWiki file URL resolver**

Helper function for extracting direct file URLs from MediaWiki sites (used with Leaguepedia).

**Function:** `get_filename_url_to_open(site, filename, size=None)`
- Resolves MediaWiki file syntax to direct URLs
- Optional size parameter for image scaling
- Used internally by other scripts for asset retrieval

## 🚧 Development Scripts

### Finding Mid Scripts *(Incomplete)*
**Advanced movement analysis**

Experimental scripts for visualizing midlaner movement patterns and team proximity analysis.

**Planned Features:**
- Midlaner pathing visualization
- Proximity heatmaps to teammates
- Time-based movement analysis
- Comparative analysis across different game states

⚠️ **Status**: Development was incomplete due to time constraints. Framework exists for extension to other roles.

## 📋 Dependencies

**Core Libraries:**
- `pandas` - Data manipulation and analysis
- `sqlalchemy` - Database integration
- `PIL (Pillow)` - Image processing
- `mwclient` - MediaWiki API interface
- `boto3` - AWS S3 integration
- `gspread` - Google Sheets API

## 🔒 Security Notes

All scripts use encrypted credentials stored in `config.py`. Sensitive information includes:
- PostgreSQL database credentials
- Google Sheets API keys
- AWS S3 access credentials
- Riot API keys (where applicable)

## ⚠️ API Deprecation Notice

Some external APIs used by these scripts are no longer available:
- Original Bayes API endpoints have changed
- S3 bucket configurations are outdated
- Some Leaguepedia API methods may have been updated

Scripts serve as reference implementation and would require API endpoint updates for current use.
