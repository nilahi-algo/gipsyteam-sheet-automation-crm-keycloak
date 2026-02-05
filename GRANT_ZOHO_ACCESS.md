# How to Grant Zoho CRM Access to Your Manager

**For:** Granting access to view Workflow Rules in Zoho CRM  
**Required Access Level:** Super Admin (you have this)  
**Target:** Manager needs access to Settings → Automation → Workflow Rules

## ⚠️ Important Distinction

**Service Admin ≠ Zoho CRM Admin**

- **Service Admins** (like in the App Settings Directory) = Admin access to specific Zoho apps (Flow, Marketing Automation, etc.)
- **Zoho CRM Admin** = Access to Zoho CRM Settings, including Workflow Rules

Your manager may already be a Service Admin for other apps, but they still need **Zoho CRM-specific access** to view Workflow Rules.

---

## First: Verify Current Access

**Ask your manager to try this:**
1. Log in to **one.zoho.com**
2. Navigate to **Zoho CRM** (not other Zoho apps)
3. Try to access: **Settings (⚙️) → Automation → Workflow Rules**

**If they can access it:** ✅ They already have the right permissions - no action needed!  
**If they cannot access it:** ❌ They need Zoho CRM access (follow steps below)

---

## Step-by-Step Instructions

### Step 1: Access User Management

1. Log in to **one.zoho.com** with your super admin account
2. Navigate to **Zoho CRM**
3. Click the **Settings** icon (⚙️) in the top right corner
4. In the left sidebar, go to **Users & Control** → **Users**

### Step 2: Add New User (if manager doesn't have an account)

**Option A: If your manager already has a Zoho account:**
1. Click **"Add Users"** or **"Invite Users"** button
2. Enter your manager's **email address** (the one associated with their Zoho account)
3. Select **"Invite Existing User"** if prompted
4. Proceed to Step 3

**Option B: If your manager needs a new account:**
1. Click **"Add Users"** or **"Invite Users"** button
2. Enter your manager's **email address**
3. Enter their **First Name** and **Last Name**
4. Select **"Create New User"** if prompted
5. They will receive an invitation email to set up their account
6. Proceed to Step 3

### Step 3: Assign Role with Settings Access

**Important:** To view Workflow Rules, the user needs access to Settings. Here are the role options:

#### Recommended: Administrator Role
1. In the user invitation/edit screen, find the **"Role"** dropdown
2. Select **"Administrator"** or **"System Administrator"**
   - This role has full access including Settings → Automation → Workflow Rules
   - ✅ **Best option** if you want them to have full visibility

#### Alternative: Custom Role with Settings Access
If you prefer to give limited access:

1. Go to **Settings** → **Users & Control** → **Roles**
2. Create a new role or edit an existing one
3. Under **"Permissions"**, ensure these are enabled:
   - ✅ **Settings** → **Automation** → **Workflow Rules** (View)
   - ✅ **Settings** → **Automation** → **Workflow Rules** (Read)
4. Assign this custom role to your manager

### Step 4: Assign Profile (if using Profiles)

1. In the user setup, find **"Profile"** dropdown
2. Select **"Administrator"** or a profile with Settings access
3. Profiles control module-level access, Roles control feature-level access

### Step 5: Complete User Setup

1. Review all settings
2. Click **"Save"** or **"Invite"**
3. Your manager will receive an email invitation (if new user)

### Step 6: Verify Access

Once your manager accepts the invitation and logs in, they should be able to:
1. Navigate to **Settings** (⚙️)
2. Go to **Automation** → **Workflow Rules**
3. View all workflow configurations

---

## Quick Access Path for Your Manager

After they log in, they should navigate to:
```
Zoho CRM → Settings (⚙️) → Automation → Workflow Rules
```

---

## Troubleshooting

### Manager can't see Settings
- **Solution:** Ensure they have Administrator role OR a custom role with Settings permissions
- Check: **Settings** → **Users & Control** → **Users** → [Manager's Name] → Verify Role

### Manager can see Settings but not Workflow Rules
- **Solution:** Check Profile permissions for Automation section
- Go to: **Settings** → **Users & Control** → **Profiles** → [Manager's Profile] → **Permissions** → **Settings** → **Automation**

### Manager needs to export workflow rules
- They can take screenshots of each workflow
- Or use browser developer tools to inspect API calls (if they have technical knowledge)
- Or you can export the workflow configuration manually

---

## Security Notes

- **Administrator role** gives full access - use only if appropriate
- Consider creating a **read-only custom role** if you only want them to view (not edit) workflows
- You can revoke access later by going to **Users** → [Manager] → **Deactivate** or **Remove**

---

## Alternative: Screen Sharing Session

If granting full access isn't preferred, you could:
1. Schedule a screen sharing session
2. Navigate to Workflow Rules together
3. Document the workflows in real-time
4. This avoids giving permanent access

---

## Next Steps

After granting access, inform your manager:
1. They should receive an invitation email
2. They need to accept the invitation and log in
3. Navigate to: **Settings** → **Automation** → **Workflow Rules**
4. They can now document the workflow configurations

---

**Need Help?** If you encounter any issues during this process, check Zoho's documentation or contact Zoho support.
