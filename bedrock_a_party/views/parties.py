from flakon import JsonBlueprint
from flask import abort, jsonify, request

from bedrock_a_party.classes.party import CannotPartyAloneError, Party, NotInvitedGuestError, \
                                            ItemAlreadyInsertedByUser, NotExistingFoodError

parties = JsonBlueprint('parties', __name__)

_LOADED_PARTIES = {}  # dict of available parties
_PARTY_NUMBER = 0  # index of the last created party


@parties.route("/parties", methods=["POST","GET"])
def all_parties():
    result = None
    if request.method == 'POST':
        try:
            result = create_party(request)
        except CannotPartyAloneError:
            abort(400, 'Cannot Party Alone!')
    elif request.method == 'GET':
        result = get_all_parties()
    return result


@parties.route("/parties/loaded", methods=["GET"])
def loaded_parties():
    return jsonify({'loaded_parties': len(_LOADED_PARTIES)})

@parties.route("/party/<id>", methods=["GET","DELETE"])
def single_party(id):
    global _LOADED_PARTIES
    result = ""
    # check if the party is an existing one
    exists_party(id)
    if 'GET' == request.method:
        # retrieve a party
        obj_party = _LOADED_PARTIES[id]
        result = obj_party.serialize()
    elif 'DELETE' == request.method:
        # delete a party
        try:
            del _LOADED_PARTIES[id]
            result = {'result':"party deleted"}
        except KeyError:
            result = {'result':"party not deleted"}
    return result


@parties.route("/party/<id>/foodlist", methods=["GET"])
def get_foodlist(id):
    global _LOADED_PARTIES
    result = ""

    # check if the party is an existing one
    exists_party(id)

    if 'GET' == request.method:
        # retrieve food-list of the party
        obj_party = _LOADED_PARTIES[id]
        result = jsonify({'foodlist': obj_party.get_food_list().serialize()})
        print(result)
    return result


@parties.route("/party/<id>/foodlist/<user>/<item>", methods=["POST","DELETE"])
def edit_foodlist(id, user, item):
    global _LOADED_PARTIES

    # check if the party is an existing one
    exists_party(id)
    #  retrieve the party
    obj_party = _LOADED_PARTIES[id]
    party = obj_party
    result = ""
    if 'POST' == request.method:
        # add item to food-list handling NotInvitedGuestError (401) and ItemAlreadyInsertedByUser (400)
        try:
            party_ret = party.add_to_food_list(item, user)
            party_ret = party_ret.serialize()
            result = party_ret
        except NotInvitedGuestError as e:
            abort(401, str(e))
        except ItemAlreadyInsertedByUser as e:
            abort(400, str(e))
    if 'DELETE' == request.method:
        # delete item to food-list handling NotExistingFoodError (400)
        try:
            party_ret = party.remove_from_food_list(item, user)
            #party_ret = party_ret.serialize()
            result = {"msg": "Food deleted!"}
        except NotExistingFoodError as e:
            abort(400, str(e))
    return result

#
# These are utility functions. Use them, DON'T CHANGE THEM!!
#

def create_party(req):
    global _LOADED_PARTIES, _PARTY_NUMBER

    # get data from request
    json_data = req.get_json()

    # list of guests
    try:
        guests = json_data['guests']
    except:
        raise CannotPartyAloneError("you cannot party alone!")

    # add party to the loaded parties lists
    _LOADED_PARTIES[str(_PARTY_NUMBER)] = Party(_PARTY_NUMBER, guests)
    _PARTY_NUMBER += 1

    return jsonify({'party_number': _PARTY_NUMBER - 1})


def get_all_parties():
    global _LOADED_PARTIES

    return jsonify(loaded_parties=[party.serialize() for party in _LOADED_PARTIES.values()])


def exists_party(_id):
    global _PARTY_NUMBER
    global _LOADED_PARTIES

    if int(_id) > _PARTY_NUMBER:
        abort(404)  # error 404: Not Found, i.e. wrong URL, resource does not exist
    elif not(_id in _LOADED_PARTIES):
        abort(410)  # error 410: Gone, i.e. it existed but it's not there anymore
