from files.helpers.wrappers import *
from files.helpers.get import *
from files.helpers.const import *
from files.classes import *
from flask import *
from files.__main__ import app, limiter, cache
from sqlalchemy.orm import joinedload
from os import environ

defaultcolor = environ.get("DEFAULT_COLOR").strip()

@app.get("/votes")
@limiter.limit("5/second;60/minute;200/hour;1000/day")
@auth_required
def admin_vote_info_get(v):
	link = request.values.get("link")
	if not link: return render_template("votes.html", v=v)

	try:
		if "t2_" in link: thing = get_post(int(link.split("t2_")[1]), v=v)
		elif "t3_" in link: thing = get_comment(int(link.split("t3_")[1]), v=v)
		else: abort(400)
	except: abort(400)

	if isinstance(thing, Submission):

		if thing.author.shadowbanned and not (v and v.admin_level):
			thing_id = g.db.query(Submission.id).filter_by(upvotes=thing.upvotes, downvotes=thing.downvotes).order_by(Submission.id).first()[0]
		else: thing_id = thing.id

		ups = g.db.query(Vote
						 ).options(joinedload(Vote.user)
								   ).filter_by(submission_id=thing_id, vote_type=1
											   ).order_by(Vote.id).all()

		downs = g.db.query(Vote
						   ).options(joinedload(Vote.user)
									 ).filter_by(submission_id=thing_id, vote_type=-1
												 ).order_by(Vote.id).all()

	elif isinstance(thing, Comment):
		if thing.author_name == '👻': abort(403)

		if thing.author.shadowbanned and not (v and v.admin_level):
			thing_id = g.db.query(Comment.id).filter_by(upvotes=thing.upvotes, downvotes=thing.downvotes).order_by(Comment.id).first()[0]
		else: thing_id = thing.id

		ups = g.db.query(CommentVote
						 ).options(joinedload(CommentVote.user)
								   ).filter_by(comment_id=thing_id, vote_type=1
											   ).order_by(CommentVote.id).all()

		downs = g.db.query(CommentVote
						   ).options(joinedload(CommentVote.user)
									 ).filter_by(comment_id=thing_id, vote_type=-1
												 ).order_by(CommentVote.id).all()

	else: abort(400)

	return render_template("votes.html",
						   v=v,
						   thing=thing,
						   ups=ups,
						   downs=downs,)



@app.post("/vote/post/<post_id>/<new>")
@limiter.limit("5/second;60/minute;600/hour;1000/day")
@auth_required
def api_vote_post(post_id, new, v):

	if new == "-1" and environ.get('DISABLE_DOWNVOTES') == '1': return {"error": "forbidden."}, 403

	if new not in ["-1", "0", "1"]: abort(400)

	if request.headers.get("Authorization"): abort(403)

	new = int(new)

	post = get_post(post_id)

	existing = g.db.query(Vote).filter_by(user_id=v.id, submission_id=post.id).one_or_none()

	if existing and existing.vote_type == new: return "", 204

	if existing:
		if existing.vote_type == 0 and new != 0:
			post.author.coins += 1
			post.author.truecoins += 1
			g.db.add(post.author)
			existing.vote_type = new
			g.db.add(existing)
		elif existing.vote_type != 0 and new == 0:
			post.author.coins -= 1
			post.author.truecoins -= 1
			g.db.add(post.author)
			g.db.delete(existing)
		else:
			existing.vote_type = new
			g.db.add(existing)
	elif new != 0:
		post.author.coins += 1
		post.author.truecoins += 1
		g.db.add(post.author)
		real = new == -1 or (not v.agendaposter and not v.shadowbanned and (bool(v.profileurl) or bool(v.customtitle) or v.namecolor != defaultcolor))
		vote = Vote(user_id=v.id,
					vote_type=new,
					submission_id=post_id,
					app_id=v.client.application.id if v.client else None,
					real = real
					)
		g.db.add(vote)

	try:
		g.db.flush()
		post.upvotes = g.db.query(Vote.id).filter_by(submission_id=post.id, vote_type=1).count()
		post.downvotes = g.db.query(Vote.id).filter_by(submission_id=post.id, vote_type=-1).count()
		post.realupvotes = g.db.query(Vote.id).filter_by(submission_id=post.id, real=True).count()
		if post.author.progressivestack: post.realupvotes *= 2
		g.db.add(post)
		g.db.commit()
	except: g.db.rollback()
	return "", 204

@app.post("/vote/comment/<comment_id>/<new>")
@limiter.limit("5/second;60/minute;600/hour;1000/day")
@auth_required
def api_vote_comment(comment_id, new, v):

	if new == "-1" and environ.get('DISABLE_DOWNVOTES') == '1': return {"error": "forbidden."}, 403

	if new not in ["-1", "0", "1"]: abort(400)

	if request.headers.get("Authorization"): abort(403)

	new = int(new)

	try: comment_id = int(comment_id)
	except:
		try: comment_id = int(comment_id, 36)
		except: abort(404)

	comment = get_comment(comment_id)

	if comment.author_id == AUTOBETTER_ID: return {"error": "forbidden."}, 403
	
	existing = g.db.query(CommentVote).filter_by(user_id=v.id, comment_id=comment.id).one_or_none()

	if existing and existing.vote_type == new: return "", 204

	if existing:
		if existing.vote_type == 0 and new != 0:
			comment.author.coins += 1
			comment.author.truecoins += 1
			g.db.add(comment.author)
			existing.vote_type = new
			g.db.add(existing)
		elif existing.vote_type != 0 and new == 0:
			comment.author.coins -= 1
			comment.author.truecoins -= 1
			g.db.add(comment.author)
			g.db.delete(existing)
		else:
			existing.vote_type = new
			g.db.add(existing)
	elif new != 0:
		comment.author.coins += 1
		comment.author.truecoins += 1
		g.db.add(comment.author)
		real = new == -1 or (not v.agendaposter and not v.shadowbanned and (bool(v.profileurl) or bool(v.customtitle) or v.namecolor != defaultcolor))
		vote = CommentVote(user_id=v.id,
						vote_type=new,
						comment_id=comment_id,
						app_id=v.client.application.id if v.client else None,
						real=real
						)

		g.db.add(vote)

	try:
		g.db.flush()
		comment.upvotes = g.db.query(CommentVote.id).filter_by(comment_id=comment.id, vote_type=1).count()
		comment.downvotes = g.db.query(CommentVote.id).filter_by(comment_id=comment.id, vote_type=-1).count()
		comment.realupvotes = g.db.query(CommentVote.id).filter_by(comment_id=comment.id, real=True).count()
		if comment.author.progressivestack: comment.realupvotes *= 2
		g.db.add(comment)
		g.db.commit()
	except: g.db.rollback()
	return "", 204


@app.post("/vote/poll/<comment_id>")
@auth_required
def api_vote_poll(comment_id, v):
	
	vote = request.values.get("vote")
	if vote == "true": new = 1
	elif vote == "false": new = 0
	else: abort(400)

	comment_id = int(comment_id)
	comment = get_comment(comment_id)

	existing = g.db.query(CommentVote).filter_by(user_id=v.id, comment_id=comment.id).one_or_none()

	if existing and existing.vote_type == new: return "", 204

	if existing:
		if new == 1:
			existing.vote_type = new
			g.db.add(existing)
		else: g.db.delete(existing)
	elif new == 1:
		vote = CommentVote(user_id=v.id, vote_type=new, comment_id=comment.id)
		g.db.add(vote)

	try:
		g.db.flush()
		comment.upvotes = g.db.query(CommentVote.id).filter_by(comment_id=comment.id, vote_type=1).count()
		g.db.add(comment)
		g.db.commit()
	except: g.db.rollback()
	return "", 204


@app.post("/bet/<comment_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def bet(comment_id, v):
	
	if v.coins < 200: return {"error": "You don't have 200 coins!"}

	vote = request.values.get("vote")
	comment_id = int(comment_id)
	comment = get_comment(comment_id)
	
	existing = g.db.query(CommentVote).filter_by(user_id=v.id, comment_id=comment.id).one_or_none()
	if existing: return "", 204

	vote = CommentVote(user_id=v.id, vote_type=1, comment_id=comment.id)
	g.db.add(vote)

	comment.upvotes += 1
	g.db.add(comment)

	v.coins -= 200
	g.db.add(v)
	autobetter = g.db.query(User).filter_by(id=AUTOBETTER_ID).one_or_none()
	autobetter.coins += 200
	g.db.add(autobetter)

	g.db.commit()
	return "", 204