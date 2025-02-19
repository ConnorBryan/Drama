from files.__main__ import app, limiter
from files.helpers.wrappers import *
from files.helpers.alerts import *
from files.helpers.get import *
from files.helpers.const import *
from files.classes.award import *
from .front import frontlist
from flask import g, request
from files.helpers.sanitize import filter_emojis_only
from copy import deepcopy

discounts = {
	69: 0.02,
	70: 0.04,
	71: 0.06,
	72: 0.08,
	73: 0.10,
}

AWARDS3 = {
	"fireflies": {
		"kind": "fireflies",
		"title": "Fireflies",
		"description": "Makes fireflies swarm the post.",
		"icon": "fas fa-sparkles",
		"color": "text-warning",
		"price": 300
	},
	"shit": {
		"kind": "shit",
		"title": "Shit",
		"description": "Makes flies swarm the post.",
		"icon": "fas fa-poop",
		"color": "text-black-50",
		"price": 300
	},
	"train": {
		"kind": "train",
		"title": "Train",
		"description": "Summons a train on the post.",
		"icon": "fas fa-train",
		"color": "text-pink",
		"price": 300
	},
	"wholesome": {
        "kind": "wholesome",
        "title": "Wholesome",
        "description": "Summons a wholesome marsey on the post.",
        "icon": "fas fa-smile-beam",
        "color": "text-yellow",
        "price": 300
    },
}

@app.get("/shop")
@app.get("/settings/shop")
@auth_required
def shop(v):
	AWARDS = deepcopy(AWARDS2)

	for val in AWARDS.values(): val["owned"] = 0

	for useraward in g.db.query(AwardRelationship).filter(AwardRelationship.user_id == v.id, AwardRelationship.submission_id == None, AwardRelationship.comment_id == None).all():
		if useraward.kind in AWARDS: AWARDS[useraward.kind]["owned"] += 1

	if v.patron == 1: discount = 0.90
	elif v.patron == 2: discount = 0.85
	elif v.patron == 3: discount = 0.80
	elif v.patron == 4: discount = 0.75
	elif v.patron == 5: discount = 0.70
	else: discount = 1

	for badge in [69,70,71,72,73]:
		if v.has_badge(badge): discount -= discounts[badge]

	for val in AWARDS.values():
		val["price"] = int(val["price"]*discount)

	sales = g.db.query(func.sum(User.coins_spent)).scalar()
	return render_template("shop.html", awards=list(AWARDS.values()), v=v, sales=sales)


@app.post("/buy/<award>")
@auth_required
def buy(v, award):
	if award == 'benefactor' and not request.values.get("mb"):
		return {"error": "You can only buy the Benefactor award with marseybux."}, 403

	AWARDS = deepcopy(AWARDS2)

	if award not in AWARDS: abort(400)
	price = AWARDS[award]["price"]

	if v.patron == 1: discount = 0.90
	elif v.patron == 2: discount = 0.85
	elif v.patron == 3: discount = 0.80
	elif v.patron == 4: discount = 0.75
	elif v.patron == 5: discount = 0.70
	else: discount = 1

	for badge in [69,70,71,72,73]:
		if v.has_badge(badge): discount -= discounts[badge]

	price = int(price*discount)

	if request.values.get("mb"):
		if v.procoins < price: return {"error": "Not enough marseybux."}, 400
		if award == "grass": return {"error": "You can't buy the grass award with marseybux."}, 403
		v.procoins -= price
	else:
		if v.coins < price: return {"error": "Not enough coins."}, 400
		v.coins -= price
		v.coins_spent += price
		if v.coins_spent >= 1000000 and not v.has_badge(73):
			new_badge = Badge(badge_id=73, user_id=v.id)
			g.db.add(new_badge)
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
			old_badge = v.has_badge(72)
			if old_badge: g.db.delete(old_badge)
		elif v.coins_spent >= 500000 and not v.has_badge(72):
			new_badge = Badge(badge_id=72, user_id=v.id)
			g.db.add(new_badge)
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
			old_badge = v.has_badge(71)
			if old_badge: g.db.delete(old_badge)
		elif v.coins_spent >= 250000 and not v.has_badge(71):
			
			new_badge = Badge(badge_id=71, user_id=v.id)
			g.db.add(new_badge)
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
			old_badge = v.has_badge(70)
			if old_badge: g.db.delete(old_badge)
		elif v.coins_spent >= 100000 and not v.has_badge(70):
			new_badge = Badge(badge_id=70, user_id=v.id)
			g.db.add(new_badge)
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
			old_badge = v.has_badge(69)
			if old_badge: g.db.delete(old_badge)
		elif v.coins_spent >= 10000 and not v.has_badge(69):
			new_badge = Badge(badge_id=69, user_id=v.id)
			g.db.add(new_badge)
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		g.db.add(v)


	if award == "lootbox":
		send_repeatable_notification(995, f"@{v.username} bought a lootbox!")
		for i in [1,2,3,4,5]:
			thing = g.db.query(AwardRelationship).order_by(AwardRelationship.id.desc()).first().id
			thing += 1
			award = random.choice(["snow", "gingerbread", "lights", "candycane", "fireplace"])
			award = AwardRelationship(id=thing, user_id=v.id, kind=award)
			g.db.add(award)
			g.db.flush()
		v.lootboxes_bought += 1
		if v.lootboxes_bought == 10 and not v.has_badge(76):
			new_badge = Badge(badge_id=76, user_id=v.id)
			g.db.add(new_badge)
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		elif v.lootboxes_bought == 50 and not v.has_badge(77):
			new_badge = Badge(badge_id=77, user_id=v.id)
			g.db.add(new_badge)
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		elif v.lootboxes_bought == 150 and not v.has_badge(78):
			new_badge = Badge(badge_id=78, user_id=v.id)
			g.db.add(new_badge)
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")

	else:
		thing = g.db.query(AwardRelationship).order_by(AwardRelationship.id.desc()).first().id
		thing += 1
		award = AwardRelationship(id=thing, user_id=v.id, kind=award)
		g.db.add(award)

	g.db.add(v)
	g.db.commit()

	return {"message": "Award bought!"}

@app.get("/post/<pid>/awards")
@app.post("/post/<pid>/awards")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def award_post(pid, v):

	if v.shadowbanned: return render_template('errors/500.html', err=True, v=v), 500
	
	kind = request.values.get("kind", "").strip()
	
	if kind not in AWARDS:
		return {"error": "That award doesn't exist."}, 404

	post_award = g.db.query(AwardRelationship).filter(
		and_(
			AwardRelationship.kind == kind,
			AwardRelationship.user_id == v.id,
			AwardRelationship.submission_id == None,
			AwardRelationship.comment_id == None
		)
	).first()

	if not post_award:
		return {"error": "You don't have that award."}, 404

	post = g.db.query(Submission).filter_by(id=pid).one_or_none()

	if not post:
		return {"error": "That post doesn't exist."}, 404

	if kind == "ghosts" and post.distinguish_level: return {"error": "You can't use the ghosts award on distinguished posts."}, 403

	post_award.submission_id = post.id
	g.db.add(post_award)

	note = request.values.get("note", "").strip()

	if v.id != post.author.id:
		msg = f"@{v.username} has given your [post]({post.permalink}) the {AWARDS[kind]['title']} Award!"
		if note: msg += f"\n\n> {note}"
		send_repeatable_notification(post.author.id, msg)

	author = post.author

	if kind == "benefactor" and author.id == v.id:
		return {"error": "You can't use this award on yourself."}, 400

	if kind == "ban":
		link = f"[this post]({post.permalink})"

		if not author.is_suspended:
			author.ban(reason=f"1-Day ban award used by @{v.username} on /post/{post.id}", days=1)
			send_repeatable_notification(author.id, f"Your account has been suspended for a day for {link}. It sucked and you should feel bad.")
		elif author.unban_utc:
			author.unban_utc += 86400
			send_repeatable_notification(author.id, f"Your account has been suspended for yet another day for {link}. Seriously man?")
	elif kind == "unban":
		if not author.is_suspended or not author.unban_utc or time.time() > author.unban_utc: abort(403)

		if author.unban_utc - time.time() > 86400:
			author.unban_utc -= 86400
			send_repeatable_notification(author.id, "Your ban duration has been reduced by 1 day!")
		else:
			author.unban_utc = 0
			author.is_banned = 0
			author.ban_evade = 0
			send_repeatable_notification(author.id, "You have been unbanned!")
	elif kind == "grass":
		author.is_banned = AUTOJANNY_ID
		author.ban_reason = f"grass award used by @{v.username} on /post/{post.id}"
		author.unban_utc = int(time.time()) + 30 * 86400
		link = f"[this post]({post.permalink})"
		send_repeatable_notification(author.id, f"Your account has been suspended permanently for {link}. You must [provide the admins](/contact) a timestamped picture of you touching grass to get unbanned!")
	elif kind == "pin":
		if post.stickied and post.stickied_utc:
			post.stickied_utc += 3600
		else:
			post.stickied = f'{v.username} (pin award)'
			post.stickied_utc = int(time.time()) + 3600
		g.db.add(post)
		cache.delete_memoized(frontlist)
	elif kind == "unpin":
		if not post.stickied_utc: abort(403)
		t = post.stickied_utc - 3600
		if time.time() > t:
			post.stickied = None
			post.stickied_utc = None
			cache.delete_memoized(frontlist)
		else: post.stickied_utc = t
		g.db.add(post)
	elif kind == "agendaposter" and not (author.agendaposter and author.agendaposter_expires_utc == 0):
		if author.username == "911roofer": abort(403)
		if author.agendaposter_expires_utc and time.time() < author.agendaposter_expires_utc: author.agendaposter_expires_utc += 86400
		else: author.agendaposter_expires_utc = int(time.time()) + 86400
		
		author.agendaposter = True
		if not author.has_badge(26):
			badge = Badge(user_id=author.id, badge_id=26)
			g.db.add(badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "flairlock":
		new_name = note[:100].replace("𒐪","")
		if not new_name and author.flairchanged:
			author.flairchanged += 86400
		else:
			author.customtitleplain = new_name
			author.customtitle = filter_emojis_only(new_name)
			if len(author.customtitle) > 1000: abort(403)
			author.flairchanged = int(time.time()) + 86400
			if not author.has_badge(96):
				badge = Badge(user_id=author.id, badge_id=96)
				g.db.add(badge)
				send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "pause":
		author.mute = True
		if not author.has_badge(68):
			new_badge = Badge(badge_id=68, user_id=author.id)
			g.db.add(new_badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "unpausable":
		author.unmutable = True
		if not author.has_badge(67):
			new_badge = Badge(badge_id=67, user_id=author.id)
			g.db.add(new_badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "marsey":
		if author.marseyawarded: author.marseyawarded += 86400
		else: author.marseyawarded = int(time.time()) + 86400
		if not author.has_badge(98):
			badge = Badge(user_id=author.id, badge_id=98)
			g.db.add(badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "pizzashill":
		if author.bird:
			return {"error": "This user is the under the effect of a conflicting award: Bird Site award."}, 404
		if author.longpost: author.longpost += 86400
		else: author.longpost = int(time.time()) + 86400
		if not author.has_badge(97):
			badge = Badge(user_id=author.id, badge_id=97)
			g.db.add(badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "bird":
		if author.longpost:
			return {"error": "This user is the under the effect of a conflicting award: Pizzashill award."}, 404
		if author.bird: author.bird += 86400
		else: author.bird = int(time.time()) + 86400
		if not author.has_badge(95):
			badge = Badge(user_id=author.id, badge_id=95)
			g.db.add(badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "eye":
		author.eye = True
		if not author.has_badge(83):
			new_badge = Badge(badge_id=83, user_id=author.id)
			g.db.add(new_badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "alt":
		author.alt = True
		if not author.has_badge(84):
			new_badge = Badge(badge_id=84, user_id=author.id)
			g.db.add(new_badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "unblockable":
		author.unblockable = True
		if not author.has_badge(87):
			new_badge = Badge(badge_id=87, user_id=author.id)
			g.db.add(new_badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		for block in g.db.query(UserBlock).filter_by(target_id=author.id).all(): g.db.delete(block)
	elif kind == "fish":
		author.fish = True
		if not author.has_badge(90):
			new_badge = Badge(badge_id=90, user_id=author.id)
			g.db.add(new_badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "progressivestack":
		if author.progressivestack: author.progressivestack += 21600
		else: author.progressivestack = int(time.time()) + 21600
		if not author.has_badge(94):
			badge = Badge(user_id=author.id, badge_id=94)
			g.db.add(badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "benefactor":
		author.patron = 1
		author.procoins += 2500
		if not v.has_badge(103):
			badge = Badge(user_id=v.id, badge_id=103)
			g.db.add(badge)
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")

	if post.author.received_award_count: post.author.received_award_count += 1
	else: post.author.received_award_count = 1
	g.db.add(post.author)

	g.db.commit()
	if request.referrer and len(request.referrer) > 1:
		if request.referrer == f'{request.host_url}submit': return redirect(post.permalink)
		elif request.referrer.startswith('/') or request.referrer.startswith(request.host_url):
			return redirect(request.referrer)
	return redirect("/")


@app.get("/comment/<cid>/awards")
@app.post("/comment/<cid>/awards")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def award_comment(cid, v):

	if v.shadowbanned: return render_template('errors/500.html', err=True, v=v), 500

	kind = request.values.get("kind", "").strip()

	if kind not in AWARDS:
		return {"error": "That award doesn't exist."}, 404

	comment_award = g.db.query(AwardRelationship).filter(
		and_(
			AwardRelationship.kind == kind,
			AwardRelationship.user_id == v.id,
			AwardRelationship.submission_id == None,
			AwardRelationship.comment_id == None
		)
	).first()

	if not comment_award:
		return {"error": "You don't have that award."}, 404

	c = g.db.query(Comment).filter_by(id=cid).one_or_none()

	if not c:
		return {"error": "That comment doesn't exist."}, 404

	if kind == "ghosts" and c.distinguish_level: return {"error": "You can't use the ghosts award on distinguished comments."}, 403

	comment_award.comment_id = c.id
	g.db.add(comment_award)

	note = request.values.get("note", "").strip()

	if v.id != c.author.id:
		msg = f"@{v.username} has given your [comment]({c.permalink}) the {AWARDS[kind]['title']} Award!"
		if note: msg += f"\n\n> {note}"
		send_repeatable_notification(c.author.id, msg)

	author = c.author

	if kind == "benefactor" and author.id == v.id:
		return {"error": "You can't use this award on yourself."}, 400

	if kind == "ban":
		link = f"[this comment]({c.permalink})"

		if not author.is_suspended:
			author.ban(reason=f"1-Day ban award used by @{v.username} on /comment/{c.id}", days=1)
			send_repeatable_notification(author.id, f"Your account has been suspended for a day for {link}. It sucked and you should feel bad.")
		elif author.unban_utc:
			author.unban_utc += 86400
			send_repeatable_notification(author.id, f"Your account has been suspended for yet another day for {link}. Seriously man?")
	elif kind == "unban":
		if not author.is_suspended or not author.unban_utc or time.time() > author.unban_utc: abort(403)

		if author.unban_utc - time.time() > 86400:
			author.unban_utc -= 86400
			send_repeatable_notification(author.id, "Your ban duration has been reduced by 1 day!")
		else:
			author.unban_utc = 0
			author.is_banned = 0
			author.ban_evade = 0
			send_repeatable_notification(author.id, "You have been unbanned!")
	elif kind == "grass":
		author.is_banned = AUTOJANNY_ID
		author.ban_reason = f"grass award used by @{v.username} on /comment/{c.id}"
		author.unban_utc = int(time.time()) + 30 * 86400
		link = f"[this comment]({c.permalink})"
		send_repeatable_notification(author.id, f"Your account has been suspended permanently for {link}. You must [provide the admins](/contact) a timestamped picture of you touching grass to get unbanned!")
	elif kind == "pin":
		if c.is_pinned and c.is_pinned_utc: c.is_pinned_utc += 3600
		else:
			c.is_pinned = f'{v.username} (pin award)'
			c.is_pinned_utc = int(time.time()) + 3600
		g.db.add(c)
	elif kind == "unpin":
		if not c.is_pinned_utc: abort(403)
		t = c.is_pinned_utc - 3600
		if time.time() > t:
			c.is_pinned = None
			c.is_pinned_utc = None
		else: c.is_pinned_utc = t
		g.db.add(c)
	elif kind == "agendaposter" and not (author.agendaposter and author.agendaposter_expires_utc == 0):
		if author.username == "911roofer": abort(403)
		if author.agendaposter_expires_utc and time.time() < author.agendaposter_expires_utc: author.agendaposter_expires_utc += 86400
		else: author.agendaposter_expires_utc = int(time.time()) + 86400
		
		author.agendaposter = True
		if not author.has_badge(26):
			badge = Badge(user_id=author.id, badge_id=26)
			g.db.add(badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "flairlock":
		new_name = note[:100].replace("𒐪","")
		if not new_name and author.flairchanged:
			author.flairchanged += 86400
		else:
			author.customtitleplain = new_name
			author.customtitle = filter_emojis_only(new_name)
			if len(author.customtitle) > 1000: abort(403)
			author.flairchanged = int(time.time()) + 86400
			if not author.has_badge(96):
				badge = Badge(user_id=author.id, badge_id=96)
				g.db.add(badge)
				send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "pause":
		author.mute = True
		if not author.has_badge(68):
			new_badge = Badge(badge_id=68, user_id=author.id)
			g.db.add(new_badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "unpausable":
		author.unmutable = True
		if not author.has_badge(67):
			new_badge = Badge(badge_id=67, user_id=author.id)
			g.db.add(new_badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "marsey":
		if author.marseyawarded: author.marseyawarded += 86400
		else: author.marseyawarded = int(time.time()) + 86400
		if not author.has_badge(98):
			badge = Badge(user_id=author.id, badge_id=98)
			g.db.add(badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "pizzashill":
		if author.bird:
			return {"error": "This user is the under the effect of a conflicting award: Bird Site award."}, 404
		if author.longpost: author.longpost += 86400
		else: author.longpost = int(time.time()) + 86400
		if not author.has_badge(97):
			badge = Badge(user_id=author.id, badge_id=97)
			g.db.add(badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "bird":
		if author.longpost:
			return {"error": "This user is the under the effect of a conflicting award: Pizzashill award."}, 404
		if author.bird: author.bird += 86400
		else: author.bird = int(time.time()) + 86400
		if not author.has_badge(95):
			badge = Badge(user_id=author.id, badge_id=95)
			g.db.add(badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "eye":
		author.eye = True
		if not author.has_badge(83):
			new_badge = Badge(badge_id=83, user_id=author.id)
			g.db.add(new_badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "alt":
		author.alt = True
		if not author.has_badge(84):
			new_badge = Badge(badge_id=84, user_id=author.id)
			g.db.add(new_badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "unblockable":
		author.unblockable = True
		if not author.has_badge(87):
			new_badge = Badge(badge_id=87, user_id=author.id)
			g.db.add(new_badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		for block in g.db.query(UserBlock).filter_by(target_id=author.id).all(): g.db.delete(block)
	elif kind == "fish":
		author.fish = True
		if not author.has_badge(90):
			new_badge = Badge(badge_id=90, user_id=author.id)
			g.db.add(new_badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "progressivestack":
		if author.progressivestack: author.progressivestack += 21600
		else: author.progressivestack = int(time.time()) + 21600
		if not author.has_badge(94):
			badge = Badge(user_id=author.id, badge_id=94)
			g.db.add(badge)
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "benefactor":
		author.patron = 1
		author.procoins += 2500
		if not v.has_badge(103):
			badge = Badge(user_id=v.id, badge_id=103)
			g.db.add(badge)
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")

	if c.author.received_award_count: c.author.received_award_count += 1
	else: c.author.received_award_count = 1
	g.db.add(c.author)

	g.db.commit()
	if request.referrer and len(request.referrer) > 1 and (request.referrer.startswith('/') or request.referrer.startswith(request.host_url)):
		return redirect(request.referrer)
	else: return redirect("/")

@app.get("/admin/awards")
@admin_level_required(2)
def admin_userawards_get(v):

	if v.admin_level != 3:
		return render_template("admin/awards.html", awards=list(AWARDS3.values()), v=v)

	return render_template("admin/awards.html", awards=list(AWARDS.values()), v=v) 

@app.post("/admin/awards")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def admin_userawards_post(v):

	try: u = request.values.get("username").strip()
	except: abort(404)

	u = get_user(u, graceful=False, v=v)

	notify_awards = {}

	latest = g.db.query(AwardRelationship).order_by(AwardRelationship.id.desc()).first()
	thing = latest.id

	for key, value in request.values.items():
		if key not in AWARDS: continue

		if value:
			
			if int(value) > 10: abort(403)

			if int(value): notify_awards[key] = int(value)

			for x in range(int(value)):
				thing += 1

				award = AwardRelationship(
					id=thing,
					user_id=u.id,
					kind=key
				)

				g.db.add(award)

	if v.id != u.id:
		text = "You were given the following awards:\n\n"
		for key, value in notify_awards.items():
			text += f" - **{value}** {AWARDS[key]['title']} {'Awards' if value != 1 else 'Award'}\n"
		send_repeatable_notification(u.id, text)

	note = ""

	for key, value in notify_awards.items():
		note += f"{value} {AWARDS[key]['title']}, "

	if len(note) > 256: return {"error": "You're giving too many awards at the same time!"}
	
	ma=ModAction(
		kind="grant_awards",
		user_id=v.id,
		target_user_id=u.id,
		_note=note[:-2]
		)
	g.db.add(ma)

	g.db.commit()

	if v.admin_level != 3: return render_template("admin/awards.html", awards=list(AWARDS3.values()), v=v)
	return render_template("admin/awards.html", awards=list(AWARDS.values()), v=v) 