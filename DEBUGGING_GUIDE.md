# VS Code Debugging Guide for Django Project

## Quick Start

### 1. Start Debugging
1. Press `F5` or click **Run and Debug** in the sidebar
2. Select **"Django: Run Server"** from the dropdown
3. The server will start in debug mode

### 2. Setting Breakpoints
- Click in the **left margin** (gutter) next to any line number
- A red dot will appear - that's your breakpoint
- The debugger will pause execution when it hits this line

### 3. Useful Breakpoint Locations

#### In `create_post` view:
- **Line with `data = json.loads(request.body)`** - Inspect incoming request data
- **Line with `author = User.objects.get(id=data['author'])`** - Check if author lookup works
- **Line with `post = Post.objects.create(...)`** - See post object before it's saved

#### In `create_user` view:
- **Line with `data = json.loads(request.body)`** - Check user input
- **Line with `user = User.objects.create(...)`** - Verify user creation

### 4. Debug Controls (When paused at breakpoint)
- **Continue (F5)**: Resume execution
- **Step Over (F10)**: Execute current line, move to next
- **Step Into (F11)**: Go inside function calls
- **Step Out (Shift+F11)**: Exit current function
- **Restart (Ctrl+Shift+F5)**: Restart debugger
- **Stop (Shift+F5)**: Stop debugging

### 5. Inspect Variables
When paused at a breakpoint, you can:
- **Hover** over any variable to see its value
- Use the **Variables panel** on the left to browse all local variables
- Use the **Watch panel** to monitor specific expressions
- Use the **Debug Console** to execute Python code in the current context

### 6. Testing with Postman

1. Start debugging (F5)
2. Set breakpoints in your views
3. Send request from Postman to trigger the breakpoint
4. Inspect variables and step through code
5. Continue or modify and restart

## Common Debugging Scenarios

### Scenario 1: Request Data Not Parsing
**Problem**: Getting errors when parsing JSON

**Debug Steps**:
1. Set breakpoint at `data = json.loads(request.body)`
2. In Debug Console, type: `request.body`
3. Check if the body is valid JSON

### Scenario 2: Author Not Found
**Problem**: Getting "Author not found" error

**Debug Steps**:
1. Set breakpoint at `author = User.objects.get(id=data['author'])`
2. Inspect `data['author']` value
3. In Debug Console, type: `User.objects.all()` to see all users
4. Verify the author ID exists

### Scenario 3: Unexpected Response
**Problem**: API returns unexpected data

**Debug Steps**:
1. Set breakpoint before the `return JsonResponse(...)` line
2. Inspect the data being returned
3. Check variable values before return

## Using pdb (Python Debugger) Manually

Add this line anywhere in your code:
```python
import pdb; pdb.set_trace()
```

When execution hits this line:
- Type `n` (next) to go to next line
- Type `s` (step) to step into function
- Type `c` (continue) to continue execution
- Type `p variable_name` to print variable value
- Type `q` (quit) to exit debugger

## Debug Configuration Options

### Django: Run Server
- Use this for normal debugging with auto-reload
- Server restarts when you save files

### Django: Run Server (No Reload)
- Use this when breakpoints aren't working properly
- No auto-reload, but more stable for debugging
- Restart manually when you change code

## Tips

1. **Use Logpoints**: Right-click in gutter → Add Logpoint
   - Logs without stopping execution
   - Example: `User created: {user.username}`

2. **Conditional Breakpoints**: Right-click breakpoint → Edit Breakpoint
   - Only breaks when condition is true
   - Example: `data['author'] == 1`

3. **Django Shell Debugging**: Use Debug Console to query database
   ```python
   from posts.models import User, Post
   User.objects.all()
   Post.objects.filter(author__id=1)
   ```

4. **Check Request Headers**: In Debug Console when paused
   ```python
   request.headers
   request.method
   request.POST
   ```

## Keyboard Shortcuts
- `F5` - Start/Continue Debugging
- `F9` - Toggle Breakpoint
- `F10` - Step Over
- `F11` - Step Into
- `Shift+F5` - Stop Debugging
- `Ctrl+Shift+D` - Open Debug View

## Troubleshooting

### Breakpoints Not Working?
1. Ensure you're using "Django: Run Server (No Reload)"
2. Check that `justMyCode` is set to `true` in launch.json
3. Verify breakpoint is on an executable line (not blank or comment)

### Can't See Variables?
1. Make sure you're paused at a breakpoint
2. Check the Variables panel is expanded
3. Try the Debug Console and type variable names

### Server Won't Start?
1. Stop any other Django servers running
2. Check port 8000 is free
3. Look at the Debug Console for error messages
