

Used instructions here: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository

This is the ticket where I requested that github remove view caches: https://support.github.com/ticket/personal/0/1611003


These are in scripts/hacks:
- [x] Kindoms.xlsx
- [x] mv_referrals.py
- [x] referrer_backfill.out
- [x] referrer_backfill.py
- [x] remove_bad_email_addres.py
- [x] send_prior_award_certificates.py

```
 alias bfg="java -jar ~/Downloads/bfg-1.14.0.jar"  
 for i in Kingdoms.xlsx mv_referrals.py referrer_backfill.out refrrer_backfill.py remove_bad_email_addrs.py send_prior_award_certificates.py
 for> do
 for> bfg --delete-files $i
 for> git reflog expire --expire=now --all && git gc --prune=now --aggressive
 for> git push —force
 for> done
```
