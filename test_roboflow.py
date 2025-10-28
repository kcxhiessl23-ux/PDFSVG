"""
Test script to verify Roboflow API connection and model loading
"""
from roboflow import Roboflow

# ========== CONFIG (from label_processor.py) ==========
ROBOFLOW_API_KEY = "L93UjMpMcsqujZ2mRU6N"
WORKSPACE = "placardcleanup"
PROJECT = "placard_cleanup-imhpc"
VERSION = 2  # Version 2 is trained and deployed

print("="*60)
print("TESTING ROBOFLOW CONNECTION")
print("="*60)

# Step 1: Initialize Roboflow
print("\n[1/5] Initializing Roboflow client...")
try:
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    print(f"✓ Roboflow client created")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# Step 2: Get workspace
print(f"\n[2/5] Loading workspace '{WORKSPACE}'...")
try:
    workspace = rf.workspace(WORKSPACE)
    print(f"✓ Workspace object: {workspace}")
    print(f"   Type: {type(workspace)}")

    # Try to get workspace name/id
    try:
        if hasattr(workspace, 'id'):
            print(f"   ID: {workspace.id}")
        if hasattr(workspace, 'name'):
            print(f"   Name: {workspace.name}")
    except:
        pass

except Exception as e:
    print(f"✗ Failed: {e}")
    print("\nPossible issues:")
    print("  - Workspace name is incorrect")
    print("  - API key doesn't have access to this workspace")
    exit(1)

# Step 3: Get project
print(f"\n[3/5] Loading project '{PROJECT}'...")
try:
    project = workspace.project(PROJECT)
    print(f"✓ Project object: {project}")
    print(f"   Type: {type(project)}")

    # Try to get project details
    try:
        if hasattr(project, 'id'):
            print(f"   ID: {project.id}")
        if hasattr(project, 'name'):
            print(f"   Name: {project.name}")
    except:
        pass

except Exception as e:
    print(f"✗ Failed: {e}")
    print("\nPossible issues:")
    print("  - Project name is incorrect")
    print("  - Project doesn't exist in this workspace")
    exit(1)

# Step 4: Get version
print(f"\n[4/5] Loading version {VERSION}...")
try:
    version = project.version(VERSION)

    if version is None:
        print(f"✗ Version {VERSION} returned None")
        print("\nPossible issues:")
        print(f"  - Version {VERSION} doesn't exist")
        print("  - Check your Roboflow dashboard for available versions")
        exit(1)

    print(f"✓ Version object: {version}")
    print(f"   Type: {type(version)}")

    # Try to get version details
    try:
        if hasattr(version, 'version'):
            print(f"   Version number: {version.version}")
        if hasattr(version, 'id'):
            print(f"   ID: {version.id}")
    except:
        pass

except Exception as e:
    print(f"✗ Failed: {e}")
    print("\nPossible issues:")
    print(f"  - Version {VERSION} doesn't exist or isn't deployed")
    exit(1)

# Step 5: Get model
print(f"\n[5/5] Getting model object...")
try:
    model = version.model

    if model is None:
        print(f"✗ Model is None")
        print("\nPossible issues:")
        print("  - No trained model exists for this version")
        print("  - Model hasn't been deployed")
        print("  - Version needs to be trained first")
        exit(1)

    print(f"✓ Model object: {model}")
    print(f"   Type: {type(model)}")

    # Check if model has predict method
    if hasattr(model, 'predict'):
        print(f"✓ Model has 'predict' method")
    else:
        print(f"✗ Model missing 'predict' method")

except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

print("\n" + "="*60)
print("✓ SUCCESS: All checks passed!")
print("="*60)
print("\nYour Roboflow configuration is correct:")
print(f"  API Key: {ROBOFLOW_API_KEY[:10]}...")
print(f"  Workspace: {WORKSPACE}")
print(f"  Project: {PROJECT}")
print(f"  Version: {VERSION}")
print("\nThe model should work in label_processor.py")
