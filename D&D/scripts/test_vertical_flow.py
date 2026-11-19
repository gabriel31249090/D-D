from fastapi.testclient import TestClient
from backend.main import create_app

def run():
    app = create_app()
    client = TestClient(app)

    # 1. Health
    h = client.get('/health')
    assert h.status_code == 200, h.text
    print('1. Health OK:', h.json()['ok'])

    # 2. Create Character
    char_payload = {
        'name': 'Aria Teste Vertical',
        'rule_set': 'dnd5e-2014',
        'class_id': 'fighter',
        'level': 1,
        'abilities': {
            'strength': 16,
            'dexterity': 14,
            'constitution': 16,
            'intelligence': 10,
            'wisdom': 12,
            'charisma': 8
        },
        'equipment': {
            'armor': 'chain_mail',
            'shield': True,
            'weapon': 'longsword'
        },
        'fighting_style': 'defense'
    }
    res_char = client.post('/api/characters', json=char_payload)
    assert res_char.status_code == 201, res_char.text
    char = res_char.json()
    char_id = char['id']
    print('2. Character Created:', char['name'], 'PV:', char['max_hp'], 'CA:', char['armor_class'])

    # 3. Create Party
    party_payload = {'name': 'Comitiva Teste Vertical', 'character_ids': [char_id]}
    res_party = client.post('/api/parties', json=party_payload)
    assert res_party.status_code == 201, res_party.text
    party = res_party.json()
    party_id = party['id']
    print('3. Party Created:', party['name'])

    # 4. Start Combat
    combat_payload = {'party_id': party_id, 'monster_ids': ['training-goblin'], 'rule_set': 'dnd5e-2014'}
    res_combat = client.post('/api/combat', json=combat_payload)
    assert res_combat.status_code == 201, res_combat.text
    combat = res_combat.json()
    combat_id = combat['id']
    print('4. Combat Started: ID', combat_id, 'Round:', combat['round'], 'Version:', combat['version'])

    # 5. Combat Action
    actor_id = combat['current_actor_id']
    actor = next(c for c in combat['combatants'] if c['id'] == actor_id)
    target = next(c for c in combat['combatants'] if c['team'] != actor['team'])
    attack_id = 'longsword' if actor['team'] == 'party' else 'training-blade'
    print('5. Actor', actor['name'], 'attacking', target['name'], 'with', attack_id)

    act_payload = {
        'type': 'attack',
        'actor_id': actor_id,
        'target_id': target['id'],
        'attack_id': attack_id,
        'expected_version': combat['version']
    }
    res_act = client.post(f'/api/combat/{combat_id}/actions', json=act_payload)
    assert res_act.status_code == 200, res_act.text
    act_res = res_act.json()
    print('Action events count:', len(act_res['events']), 'New version:', act_res['combat']['version'])

    # 6. Events check
    res_events = client.get(f'/api/combat/{combat_id}/events?after_sequence=0')
    assert res_events.status_code == 200
    print('6. Events retrieved:', len(res_events.json()))

    # 7. Dice Roll
    res_dice = client.post('/api/dice/roll', json={'expression': '2d6+3', 'mode': 'normal'})
    assert res_dice.status_code == 201
    print('7. Dice roll 2d6+3 result:', res_dice.json()['total'])
    print('ALL INTEGRATION CHECKS COMPLETED SUCCESSFULLY!')

if __name__ == '__main__':
    run()
