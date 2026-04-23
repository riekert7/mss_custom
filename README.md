# MSS Custom

Frappe custom app for MSS — packages custom fields, scripts, print formats, and Issue workflow logic so they can be migrated consistently between dev and production.

## What it includes

### Issue workflow hooks

Hooks registered on the `Issue` doctype:

| Event | Handler | Purpose |
|-------|---------|---------|
| `before_print` | `issue.before_print_issue` | Custom logic applied before printing an Issue |
| `validate` | `issue_users.validate_issue_users` | Validates the Issue Users child table |
| `on_update` | `issue_users.handle_issue_users_changes` | Syncs user assignments when the Issue is saved |
| `on_update` | `issue.handle_issue_updates` | Handles other update side-effects |

### Issue Users doctype

A child table that tracks which users are assigned to each Issue, with change detection on save.

### Fixtures

Exported and imported automatically via `bench migrate`, so all customisations survive reinstalls across environments:

- Custom Fields (module: MSS Custom)
- Server Scripts (enabled only)
- Client Scripts (enabled only)
- DocTypes
- Print Formats

### Desk assets

- Custom CSS loaded in the desk header (`mss_custom.css`)
- Custom JS loaded on all desk pages (`issue.js`)

## Installation

```bash
bench get-app https://github.com/riekert7/mss_custom
bench --site [sitename] install-app mss_custom
bench --site [sitename] migrate
```

## License

MIT