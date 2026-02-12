# Quick Start Guide - Hitachi Website Data Collection

## 🚀 Required Steps

**ALWAYS run from the correct directory:**

```powershell
cd C:\Users\snarayan\Desktop\electrical-bushing-agent\data_collection\hitachi_website_data_collection
python hitachi_website_data_batch_scraper.py --start 1 --end 100 --delay 0.5
```

**That's it!** Just make sure you're in the `hitachi_website_data_collection/` directory before running any Python commands.

---

## � Write Modes

The scraper supports three write modes (default is `append`):

| Mode | Flag | Behavior | Use Case |
|------|------|----------|----------|
| **Append** | `--mode append` | Skips indices in CSV, HTML, or error log | Default, incremental data collection |
| **Overwrite** | `--mode overwrite` | Overwrites existing data, skips error log indices | Update specific entries |
| **Scratch** | `--mode scratch` | Deletes ALL data and starts fresh | Complete reset ⚠️ |

**Note**: All modes automatically skip indices in the error log and delete their HTML files if encountered.

**Default behavior**: If you don't specify `--mode`, it will use `append` mode (skip existing data).

---

## �🐛 Troubleshooting

### Issue: "Can't open file" or "No such file or directory"

**Cause**: Running from wrong directory

**Fix**: Always navigate to the correct directory first:
```powershell
cd C:\Users\snarayan\Desktop\electrical-bushing-agent\data_collection\hitachi_website_data_collection
```

### Issue: "ModuleNotFoundError: No module named 'pandas'"

**Cause**: Wrong Python environment

**Fix**: Make sure you're using the Anaconda base environment. You should see `(base)` in your terminal prompt.

---

## 📊 Common Operations

### Test with Small Range
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 10 --delay 0.5
```

### Production Run (Large Scale)
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 50000 --delay 0.5
```

### Specific Indices
```powershell
python hitachi_website_data_batch_scraper.py --indices 42131,42246,50000
```

### Single Index
```powershell
python hitachi_website_data_scraper.py 42131
**Remember**: Always navigate to the directory first!

```powershell
cd C:\Users\snarayan\Desktop\electrical-bushing-agent\data_collection\hitachi_website_data_collection
```

**Then run any of these commands:**

### Test with Small Range
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 10 --delay 0.5
```

### Medium Batch
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 10

## 📁 Output Files

All files are created in the current directory (`hitachi_website_data_collection/`):

```
✓ hitNavigate to directory**:
   ```powershell
   cd C:\Users\snarayan\Desktop\electrical-bushing-agent\data_collection\hitachi_website_data_collection
   ```

2. **Verify you're in correct location**:
   ```powershell
   pwd  # Should show: ...\hitachi_website_data_collection
   ```

3. **Test with small range**:
   ```powershell
   python hitachi_website_data_batch_scraper.py --start 1 --end 5 --delay 0.5
   ```

4. **Check output**:
   ```powershell
   ls hitachi_website_bushing_master_list.csv
   ls hitachi_website_data_raw\cross_reference_data\
   ```

5  ```

2. **Test with small range**:
   ```powershell
   python hitachi_website_data_batch_scraper.py --start 1 --end 5
   ```

3. **Check output**:
   ```powershell
   ls hitachi_website_bushing_master_list.csv
   ls hitachi_website_data_raw\cross_reference_data\
   ```

4. **Review errors** (if any):
   ```powershell
   Import-Csv hitachi_website_scraping_error_log.csv | Format-Table
   ```

---

## 🔧 Useful PowerShell Commands

**Count scraped records**:
```powershell
(Import-Csv hitachi_website_bushing_master_list.csv).Count
```

**Count HTML files**:
```powershell
(Get-ChildItem hitachi_website_data_raw\cross_reference_data\*.html).Count
```

**View error summary** (count by message pattern):
```powershell
Import-Csv hitachi_website_scraping_error_log.csv | Group-Object { $_.Error_Message.Substring(0, [Math]::Min(30, $_.Error_Message.Length)) } | Format-Table Name, Count
```

**View recent errors**:
```powershell
Import-Csv hitachi_website_scraping_error_log.csv | Select-Object -Last 10 | Format-Table
```

---

## 💡 Tips

1. **Always navigate to the website directory first** - prevents "file not found" errors
2. **Use append mode by default** - automatically skips already-scraped indices and error log
3. **Use delay 0.5-1.0 seconds** - be respectful to the server
4. **Test with small range first** - verify everything works before large runs
5. **Monitor error log** - helps identify problematic index ranges and saves time
6. **Error log is preserved** - never cleared between runs, provides performance benefit
7. **Use overwrite mode sparingly** - only when you need to update specific entries
8. **Use scratch mode with caution** - it deletes ALL existing data including error log
9. **HTML files auto-cleanup** - error index HTML files deleted when encountered
10. **Only valid data saved** - HTML files only for bushings with actual data (saves space)

---

## 📞 Need Help?

Check the detailed documentation:
- [README.md](README.md) - Full documentation
- [../README.md](../README.md) - Multi-website system overview
- [../REORGANIZATION_SUMMARY.md](../REORGANIZATION_SUMMARY.md) - Migration guide

---

**Last Updated**: February 11, 2026  
**Version**: 3.2 - Performance optimized with smart error log handling
