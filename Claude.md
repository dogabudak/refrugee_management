# Refugee Management / Strategy Game Backend

## Project Overview

This is a Django-based backend service for a Call of War-like browser/mobile grand strategy game. The system is split into two main concerns:

1. **Asset/Content Management** (handled in another project) - Static game content, item definitions, unit stats, etc.
2. **Game State Management** (THIS PROJECT) - Real-time game state, tick-based updates, and player interactions

## Architecture

### Core Systems

#### 1. Game State Management
- **WorldState**: Snapshot of the entire game world at a specific tick
- **Tick System**: Time-based progression (e.g., 1 tick = 15 minutes)
- **State Persistence**: Storing and retrieving game states efficiently
- **State Transitions**: Calculating next state based on player actions and game rules

#### 2. Real-time Updates
- Periodic tick processing
- Player action queuing and validation
- Event-driven state changes
- WebSocket/polling for client updates

#### 3. Player Interactions
- Command issuance (move units, build, research, diplomacy)
- Action validation and resolution
- Multi-player coordination
- Alliance and diplomacy system

### Data Model Overview

```
Game (game instance)
  └─ WorldState (game state snapshots)
      ├─ HexTiles (hexagonal map tiles)
      │   ├─ Terrain
      │   ├─ Items/Loot
      │   ├─ Structures
      │   └─ Interactables
      ├─ Characters/Units (player characters and NPCs)
      │   ├─ Hex Position
      │   ├─ Inventory
      │   ├─ Status
      │   └─ Orders
      ├─ Players
      │   ├─ Resources
      │   ├─ Research
      │   └─ Characters
      └─ GlobalEvents
```

## Technical Stack

- **Framework**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL (configurable, currently SQLite for dev)
- **API Documentation**: drf-spectacular (OpenAPI 3)
- **Dependency Management**: Poetry
- **Python**: 3.10+

## Key Concepts

### Tick-Based Gameplay

The game progresses in discrete time intervals called "ticks". Each tick:
1. Processes all player commands from the queue
2. Executes game logic (movement, combat, production, research)
3. Generates new WorldState
4. Notifies clients of changes

### State Immutability

WorldState records should be immutable once created. This allows:
- Historical replay of game progression
- Debugging and analytics
- Rollback in case of errors
- Audit trail for anti-cheat

### Command Queue

Player actions are queued and processed during tick resolution:
- **Immediate validation**: Check if command is legal at submission time
- **Deferred execution**: Apply command effects during next tick
- **Conflict resolution**: Handle simultaneous conflicting commands

## API Structure

### Endpoints

```
/api/schema/          - OpenAPI schema
/api/docs/            - Swagger UI
/api/redoc/           - ReDoc UI

/api/games/           - Game instances
/api/games/{id}/state/           - Current world state
/api/games/{id}/commands/        - Submit player commands
/api/games/{id}/map/             - Hex map data
/api/games/{id}/tiles/           - Individual hex tile data
/api/games/{id}/characters/      - Character/unit data
/api/games/{id}/players/         - Player data
/api/games/{id}/loot/            - Available loot/items on map
```

## Development Guidelines

### Models
- Use JSONField for flexible nested data structures
- Include timestamps (created_at, updated_at)
- Add indexes on frequently queried fields
- Use django-model-utils for common patterns

### Serializers
- Separate read/write serializers when needed
- Include proper validation
- Use nested serializers for related data

### Views
- Use viewsets for CRUD operations
- Implement custom actions for game-specific operations
- Add proper permissions and authentication
- Document with drf-spectacular decorators

### Testing
- Unit tests for game logic
- Integration tests for tick processing
- API tests for all endpoints
- Load tests for concurrent player actions

## Performance Considerations

1. **Database Optimization**
   - Use select_related/prefetch_related for queries
   - Implement caching for frequently accessed data
   - Consider read replicas for high traffic

2. **Tick Processing**
   - Batch database operations
   - Use transactions appropriately
   - Process actions in parallel where possible
   - Queue heavy computations

3. **Real-time Updates**
   - Use WebSockets or Server-Sent Events
   - Implement delta updates (only changed data)
   - Rate limit client requests

## Future Enhancements

- [ ] Event sourcing for complete game history
- [ ] Distributed tick processing for scalability
- [ ] Redis for caching and pub/sub
- [ ] Celery for async task processing
- [ ] GraphQL API as alternative to REST
- [ ] Real-time spectator mode
- [ ] AI opponents
- [ ] Replay system

## Related Projects

- **Content Management Service**: Handles static game assets (items, unit definitions, map data)
- **Frontend Client**: Browser/mobile game interface
- **Analytics Service**: Game metrics and player behavior analysis

## Getting Started

```bash
# Install dependencies
poetry install

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Access API docs
http://localhost:8000/api/docs/
```

## Common Commands

```bash
# Create new app
python manage.py startapp <app_name>

# Make migrations
python manage.py makemigrations

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Process game tick (custom command - to be implemented)
python manage.py process_tick <game_id>
```
