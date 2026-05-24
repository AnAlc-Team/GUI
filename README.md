```mermaid
flowchart LR
  Sleep[Sleep] --> Wake{Awake?}
  Wake -->|No| Sleep
  Wake -->|Hungry| Snack[Get treat]
  Wake -->|Not in in Sun?| Move[Move to sun]
  Wake -->|Human is typing| Keyboard[Sleep on keyboard]
  Wake -->|Yes| House[Go to Kostas house]
  House --> Sleep
  Snack --> Sleep
  Move --> Sleep
  Keyboard --> Sleep
```
