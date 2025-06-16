### Gathering match and training data
I developed this code during my time as a data analyst for esport teams around 2022-2023.
It gathered match data from Bayes API and sent it to Postgres database.

## Database Architecture

The system uses **two separate PostgreSQL databases** with identical schemas:
- **OFFICIAL_GAMES**: Professional league matches (LCS, LEC, LCK, etc.)
- **SCRIMS**: Practice matches and scrimmages

### Database Schema Overview

📊 **[View Database Schema Diagram](diagrams/database_scheme.drawio.png)**

#### Core Tables

**🔑 player_stats** - Individual player performance data
- Player identifiers, match info, league data
- Champion, role, side, team information
- Game performance: KDA, CS, gold share, damage share
- Time-based stats: first blood, level 6 timer
- Proximity analytics: support/jungle positioning
- Early game snapshots (8min/14min intervals)

**🔑 team_stats** - Team-level match statistics
- Team identifiers and match results
- Economic metrics: gold differential, resource control
- Objective control: dragons, barons, heralds
- Structure control: towers, plates, first objectives
- Strategic timing metrics

**🔑 drafts** - Pick/ban phase data
- Complete draft sequence (10 bans, 10 picks)
- Role assignments for each pick
- Team compositions and strategies
- S3 replay file links (ROFL format)

#### Player Build Tables

**🔑 items** - End-game item builds
- 6 item slots + trinket per player
- Item acquisition timestamps
- Build path analysis data

**🔑 runes** - Rune configurations
- Complete rune setups (6 runes per player)
- Rune statistics and variables
- Build optimization data

#### Position & Event Tables

**🔑 proximity_timeline** - Player positioning over time
- Real-time player coordinates
- Role proximity calculations
- Team coordination metrics

**🔑 event_positions** - Player positions during objectives
- Positioning around major objectives
- Player states (alive/dead) during events
- Strategic positioning analysis

**🔑 events** - Major game objectives
- Dragon, baron, herald, tower events
- Objective timing and team coordination
- Gold expenditure around objectives

**🔑 wards** - Vision control data
- Ward placement and destruction events
- Vision control patterns
- Support and jungle pathing

#### Support Tables

**🔑 player_info** - Player metadata (from Leaguepedia)
- Player names, roles, teams
- Regional information
- Professional player database

**🔑 league_info** - League configuration
- Supported leagues and regions
- Timeline data collection settings

**🔑 games_with_error** - Error tracking
- Failed match processing
- Data quality monitoring

### Data Features

- **Comprehensive Analytics**: Player performance, team strategies, draft analysis
- **Positional Data**: Real-time player positioning and coordination metrics
- **Build Analysis**: Items, runes, and optimization patterns
- **Objective Control**: Detailed tracking of major game objectives
- **Vision Control**: Ward placement and map control analysis
- **Replay Integration**: Automated ROFL file storage in S3
- **Error Handling**: Robust error tracking and data quality monitoring

Other utilities are located in the scripts folder with separate readme in which I briefly explain their functionality.
