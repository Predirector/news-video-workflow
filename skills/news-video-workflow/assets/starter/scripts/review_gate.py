"""Require an explicit, file-backed review record before final cleanup."""
from pathlib import Path
CHECKS=['cover','fonts','mobileTypography','evidenceAndMaterials','captionsAndHolds','transitionsAndFlash','musicAndSync']
def validate_review(review,root,media):
 if review.get('passed') is not True:raise ValueError('Review has not passed')
 if review.get('unresolved'):raise ValueError('Resolve outstanding review findings before cleanup')
 checked=review.get('checkedFiles',[])
 if not checked:raise ValueError('Record actual checkedFiles, not a generic passed flag')
 for entry in checked:
  p=Path(entry)
  if not p.is_absolute():p=(media if p.parts and p.parts[0] in ['output','public'] else root)/p
  p=p.resolve()
  if not(p.is_relative_to(root.resolve()) or p.is_relative_to(media.resolve())) or not p.is_file():raise ValueError('Reviewed file absent or outside this episode: '+entry)
 for key in CHECKS:
  item=review.get('checks',{}).get(key,{})
  if item.get('status') not in ['passed','not_applicable'] or not item.get('notes'):raise ValueError('Record a specific review outcome for '+key)
 return True
