import pandas as pd
from app import db  # Adjust this import based on where your db instance lives
from app.models import Hotel, Room


class DBSeedHelper:

    @staticmethod
    def seed_hotels_and_rooms_from_csv(csv_path="data/room_qty.csv"):
        """
        Reads room_qty.csv and seeds the Hotel and Room tables into the DB.
        """
        try:
            # Read the CSV
            df = pd.read_csv(csv_path)

            # ==========================================
            # 🚨 FILTER OUT DROPPED PROPERTIES
            # ==========================================
            properties_to_drop = [194837, 194842, 179195, 243134, 307448]
            if "property_id" in df.columns:
                df = df[~df["property_id"].isin(properties_to_drop)].copy()

            # If your CSV uses 'id' instead of 'room_id', rename it for consistency
            if "id" in df.columns and "room_id" not in df.columns:
                df = df.rename(columns={"id": "room_id"})

            # ==========================================
            # 1. SEED HOTELS FIRST (Foreign Key Parent)
            # ==========================================
            print("Seeding Hotels...")
            hotels_df = df[["property_id", "property_name"]].drop_duplicates().dropna()

            for _, row in hotels_df.iterrows():
                h_id = int(row["property_id"])
                # Check if it already exists to prevent crashes
                existing_hotel = db.session.get(Hotel, h_id)

                if not existing_hotel:
                    new_hotel = Hotel(id=h_id, name=str(row["property_name"]))
                    db.session.add(new_hotel)

            # Commit the hotels so the Rooms have valid Foreign Keys to point to!
            db.session.commit()
            print("✅ Hotels seeded successfully!")

            # ==========================================
            # 2. SEED ROOMS (Foreign Key Child)
            # ==========================================
            print("Seeding Rooms...")
            rooms_df = (
                df[["room_id", "room_name", "property_id"]].drop_duplicates().dropna()
            )

            for _, row in rooms_df.iterrows():
                r_id = int(row["room_id"])
                existing_room = db.session.get(Room, r_id)

                if not existing_room:
                    new_room = Room(
                        id=r_id,
                        name=str(row["room_name"]),
                        property_id=int(row["property_id"]),
                    )
                    db.session.add(new_room)

            db.session.commit()
            print("✅ Rooms seeded successfully!")

        except Exception as e:
            db.session.rollback()
            print(f"❌ An error occurred during seeding: {e}")

    @staticmethod
    def print_all_data():
        """
        Function to print hotels and rooms available in DB
        """
        hotels = db.session.query(Hotel).all()
        print(f"\n--- Found {len(hotels)} Hotels ---")
        for hotel in hotels:
            print(f"Hotel ID : {hotel.id} | Name : {hotel.name}")

        rooms = db.session.query(Room).all()
        print(f"\n--- Found {len(rooms)} Rooms ---")
        for room in rooms:
            print(
                f"Room ID : {room.id} | Name : {room.name} | Property ID : {room.property_id}"
            )

        if len(hotels) == 0 and len(rooms) == 0:
            print("No Records Found")


from app import db
from app.models import Hotel


class HotelDetailSeeder:
    @staticmethod
    def seed_hotel_details():
        """
        Updates specific hotels with carefully summarized 1-paragraph descriptions,
        ratings, image links, coordinates, and booking/maps links.
        """
        hotel_details = [
            {
                "id": 158986,
                "name": "Abams Gili Air",
                "description": "Terletak di Gili Air dekat Pantai Gili Air dan Pelabuhan Bangsal, Abams Gili Air menawarkan B&B berfasilitas lengkap dengan WiFi gratis, AC, teras, kamar mandi bershower, pilihan sarapan harian, serta layanan rental sepeda dan mobil.",
                "rating": 8.1,
                "image_link": "static/348460500.jpg",
                "maps_link": "https://maps.app.goo.gl/5aH6kaBUEbwcNWpB8",
                "latitude": -8.361528188101731,
                "longitude": 116.08056399375027,
                "booking_link": "https://www.booking.com/hotel/id/abams-gili-air.id.html?aid=356980&label=gog235jc-10CAsoaEIOYWJhbXMtZ2lsaS1haXJIElgDaGiIAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4Av_uhtAGwAIB0gIkYWYyZDRlMmEtMzk3ZS00NTM0LTk5ZTktNDRkZWQ2NGI4MzY12AIB4AIB&sid=6347ace0c5d563e26922a9ae342bc248&age=0&checkin=2026-05-11&checkout=2026-05-12&dest_id=900048668&dest_type=city&dist=0&group_adults=2&group_children=0&hapos=1&hpos=1&no_rooms=1&req_adults=2&req_children=0&room1=A%2CA&sb_price_type=total&soh=1&sr_order=popularity&srepoch=1778497436&srpvid=329d4dc03c3700e6&type=total&ucfs=1&#no_availability_msg",
            },
            {
                "id": 158990,
                "name": "Pandan Bungalow",
                "description": "Pandan Bungalow yang terletak beberapa langkah dari Pantai Gili Air menawarkan akomodasi nyaman dengan kolam renang outdoor, area pantai pribadi, restoran, layanan kamar, WiFi gratis, serta kamar-kamar ber-AC yang menyuguhkan pemandangan taman.",
                "rating": 7.9,
                "image_link": "static/248990987.jpg",
                "maps_link": "https://maps.app.goo.gl/H1gdytg6m96toSB89",
                "latitude": -8.355123561279564,
                "longitude": 116.07650729622887,
                "booking_link": "https://www.booking.com/hotel/id/pandan-bungalow.id.html?aid=356980&label=gog235jc-10CAsoaEIPcGFuZGFuLWJ1bmdhbG93SBJYA2hoiAEBmAEzuAEXyAEM2AED6AEB-AEBiAIBqAIBuAKz9IbQBsACAdICJDMyNWMyMTNiLWYyNWYtNGJhOS04MDI2LTJhMGUyZmIwNjFmY9gCAeACAQ&sid=6347ace0c5d563e26922a9ae342bc248&age=0&all_sr_blocks=90869402_121171619_0_1_0_478242&checkin=2026-05-16&checkout=2026-05-17&dest_id=900048668&dest_type=city&dist=0&group_adults=2&group_children=0&hapos=1&highlighted_blocks=90869402_121171619_0_1_0_478242&hpos=1&matching_block_id=90869402_121171619_0_1_0_478242&no_rooms=1&req_adults=2&req_children=0&room1=A%2CA&sb_price_type=total&sr_order=popularity&sr_pri_blocks=90869402_121171619_0_1_0_478242_61875000&srepoch=1778498127&srpvid=3f5c4f1ad1f60610&type=total&ucfs=1&#map_closed",
            },
            {
                "id": 161014,
                "name": "Mantra Gili",
                "description": "Berlokasi di Gili Trawangan dekat lokasi populer, Mantra Gili menyediakan kamar-kamar ber-AC yang dilengkapi TV, brankas, dan kamar mandi pribadi, ditambah fasilitas kolam renang outdoor, WiFi gratis, pilihan sarapan harian, serta rental kendaraan.",
                "rating": 9.0,
                "image_link": "static/402678080.jpg",
                "maps_link": "https://maps.app.goo.gl/ySNRx4i6Vki1udvDA",
                "latitude": -8.352757911307336,
                "longitude": 116.04086899560043,
                "booking_link": "https://www.booking.com/hotel/id/mantra-gili.id.html?aid=356980&label=gog235jc-10CAsoaEILbWFudHJhLWdpbGlIElgDaGiIAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4AuLzhtAGwAIB0gIkMDRlNGQyNWItZjlhMC00NDRiLWEwOWUtYzY3NmI4MWU2N2U12AIB4AIB&sid=6347ace0c5d563e26922a9ae342bc248&age=0&all_sr_blocks=590300905_0_2_0_0&checkin=2026-05-16&checkout=2026-05-17&dest_id=900048659&dest_type=city&dist=0&group_adults=2&group_children=0&hapos=1&highlighted_blocks=590300905_0_2_0_0&hpos=1&matching_block_id=590300905_0_2_0_0&no_rooms=1&req_adults=2&req_children=0&room1=A%2CA&sb_price_type=total&sr_order=popularity&sr_pri_blocks=590300905_0_2_0_0__48948174&srepoch=1778498075&srpvid=17854ef2e6c10302&type=total&ucfs=1&",
            },
            {
                "id": 163277,
                "name": "Kaluku Gili Resort",
                "description": "Menawarkan bungalow tradisional terinspirasi gudang beras dengan pemandangan laut atau gunung, Kaluku Gili Resort terletak hanya 2 menit dari Pantai Gili Air dan dilengkapi dengan fasilitas modern, kolam renang, layanan pijat, serta akses mudah ke berbagai aktivitas air.",
                "rating": 8.9,
                "image_link": "static/250240723.jpg",
                "maps_link": "https://maps.app.goo.gl/nezJrYhWuduTPV6B8",
                "latitude": -8.353409846449411,
                "longitude": 116.08658583792896,
                "booking_link": "https://www.booking.com/hotel/id/kaluku-gili-resort.id.html?aid=356980&label=gog235jc-10CAsoaEISa2FsdWt1LWdpbGktcmVzb3J0SBJYA2hoiAEBmAEzuAEXyAEM2AED6AEB-AEBiAIBqAIBuAKe84bQBsACAdICJGQzYzdhNmY1LTQ1NmEtNDkzZS1hMjk5LTZjYzgxMmE1Y2RhN9gCAeACAQ&sid=6347ace0c5d563e26922a9ae342bc248&age=0&checkin=2026-05-16&checkout=2026-05-17&dest_id=900048668&dest_type=city&dist=0&group_adults=2&group_children=0&hapos=1&hpos=1&no_rooms=1&req_adults=2&req_children=0&room1=A%2CA&sb_price_type=total&soh=1&sr_order=popularity&srepoch=1778498002&srpvid=ffa44ecf783904d6&type=total&ucfs=1&#no_availability_msg",
            },
            {
                "id": 169082,
                "name": "Bougenville Homestay",
                "description": "Bougenville Homestay menawarkan akomodasi nyaman dengan restoran, taman, teras, WiFi gratis, dan kamar mandi pribadi, berlokasi ideal bagi Anda yang ingin menikmati kegiatan snorkeling atau mengunjungi berbagai atraksi di sekitarnya.",
                "rating": 8.4,
                "image_link": "static/855549673.jpg",
                "maps_link": "https://maps.app.goo.gl/P79hLX5D9uqDKL3Q7",
                "latitude": -8.70943227115207,
                "longitude": 116.07625079925285,
                "booking_link": "https://www.booking.com/hotel/id/villa-bougenville-gerung1.id.html?aid=356980&label=gog235jc-10CAsoaEIZdmlsbGEtYm91Z2VudmlsbGUtZ2VydW5nMUgSWANoaIgBAZgBM7gBF8gBDNgBA-gBAfgBAYgCAagCAbgCi_CG0AbAAgHSAiRjNzI3OWMyYi03ZTkwLTQ0ZDMtYmExNy03YmE0OWFlZmQ3N2XYAgHgAgE&sid=6347ace0c5d563e26922a9ae342bc248&all_sr_blocks=884900010_399334399_0_2_0_468720&checkin=2026-05-11&checkout=2026-05-12&dest_id=-2684928&dest_type=city&dist=0&group_adults=2&group_children=0&hapos=1&highlighted_blocks=884900010_399334399_0_2_0_468720&hpos=1&matching_block_id=884900010_399334399_0_2_0_468720&no_rooms=1&req_adults=2&req_children=0&room1=A%2CA&sb_price_type=total&sr_order=popularity&sr_pri_blocks=884900010_399334399_0_2_0_468720_41580000&srepoch=1778497676&srpvid=69f04e06f2a701f6&type=total&ucfs=1&",
            },
            {
                "id": 174792,
                "name": "Shefa Private Villa",
                "description": "Shefa Private Villa di Gili Trawangan menawarkan pengalaman menginap eksklusif dengan kolam renang pribadi, dapur lengkap, dan area keluarga dalam vila 1 kamar tidur ber-AC yang juga menyediakan sepeda gratis, WiFi gratis, serta sarapan harian.",
                "rating": 9.1,
                "image_link": "static/412129557.jpg",
                "maps_link": "https://maps.app.goo.gl/Y3dH6TVTyJnCPv9KA",
                "latitude": -8.346680839712736,
                "longitude": 116.03622466491413,
                "booking_link": "https://www.booking.com/hotel/id/shefa-private-villa-kabupaten-lombok-utara.id.html?aid=356980&label=gog235jc-10CAsoaEIqc2hlZmEtcHJpdmF0ZS12aWxsYS1rYWJ1cGF0ZW4tbG9tYm9rLXV0YXJhSBJYA2hoiAEBmAEzuAEXyAEM2AED6AEB-AEBiAIBqAIBuAKv9YbQBsACAdICJGU5ODI5NjEwLTNmNmQtNDRkMi04MzI3LWU0NjcxYjk4ZGZjYdgCAeACAQ&sid=6347ace0c5d563e26922a9ae342bc248&age=0&all_sr_blocks=924380901_427235580_0_2_0&checkin=2026-05-16&checkout=2026-05-17&dest_id=900048659&dest_type=city&dist=0&group_adults=2&group_children=0&hapos=1&highlighted_blocks=924380901_427235580_0_2_0&hpos=1&matching_block_id=924380901_427235580_0_2_0&no_rooms=1&req_adults=2&req_children=0&room1=A%2CA&sb_price_type=total&sr_order=popularity&sr_pri_blocks=924380901_427235580_0_2_0__183330000&srepoch=1778498250&srpvid=9b264f587ada04c1&type=total&ucfs=1&",
            },
            {
                "id": 193394,
                "name": "Bintang Darmawan Villa (BDV)",
                "description": "Bintang Darmawan Villa (BDV) di Gili Trawangan menawarkan penginapan nyaman dengan kolam renang outdoor, teras, dan bar. Berjarak dekat dari Pantai Timur Laut dan Pelabuhan Gili Trawangan, hotel ini menyediakan kamar-kamar ber-AC berfasilitas lengkap dengan WiFi gratis, serta akses mudah untuk menjelajahi pulau.",
                "rating": 8.2,
                "image_link": "static/125976922.jpg",
                "maps_link": "https://maps.app.goo.gl/eCPQ5qox8yxNGKdF6",
                "latitude": -8.351124710775863,
                "longitude": 116.04090026807471,
                "booking_link": "https://www.booking.com/hotel/id/bintang-darmawan-villa.id.html?aid=356980&label=gog235jc-10CAsoaEIWYmludGFuZy1kYXJtYXdhbi12aWxsYUgSWANoaIgBAZgBM7gBF8gBDNgBA-gBAfgBAYgCAagCAbgCwe-G0AbAAgHSAiQ1Y2U3NzllOS1hMmVkLTQ3ZDEtODQwNy1lNDk4MzljMjU0MTXYAgHgAgE&sid=6347ace0c5d563e26922a9ae342bc248&age=0&all_sr_blocks=289509401_108864661_0_42_0&checkin=2026-05-11&checkout=2026-05-12&dest_id=900048659&dest_type=city&dist=0&group_adults=2&group_children=0&hapos=1&highlighted_blocks=289509401_108864661_0_42_0&hpos=1&matching_block_id=289509401_108864661_0_42_0&no_rooms=1&req_adults=2&req_children=0&room1=A%2CA&sb_price_type=total&sr_order=popularity&sr_pri_blocks=289509401_108864661_0_42_0__42519500&srepoch=1778497521&srpvid=39dc4de16f310036&type=total&ucfs=1&",
            },
            {
                "id": 201589,
                "name": "Bungalow No 7",
                "description": "Terletak di tepi pantai Nusa Lembongan yang tenang, Bungalow No 7 adalah akomodasi kelolaan keluarga yang dikelilingi taman tropis. Menawarkan kamar ber-AC dengan interior kayu bernuansa alam, resor ini juga dilengkapi dengan restoran, fasilitas kelas menyelam, wisata snorkeling, dan akses dekat ke titik selancar populer.",
                "rating": 7.8,
                "image_link": "static/28671898.jpg",
                "maps_link": "https://maps.app.goo.gl/3WTP44PpBBmX6xfp8",
                "latitude": -8.67718377070046,
                "longitude": 115.44654963978579,
                "booking_link": "https://www.agoda.com/id-id/bungalow-no-7/hotel/bali-id.html?countryId=192&finalPriceView=1&isShowMobileAppPrice=false&cid=1833981&numberOfBedrooms=&familyMode=false&adults=2&children=0&rooms=1&maxRooms=0&checkIn=2026-05-16&isCalendarCallout=false&childAges=&numberOfGuest=0&missingChildAges=false&travellerType=1&showReviewSubmissionEntry=false&currencyCode=IDR&isFreeOccSearch=false&los=1&searchrequestid=4e01154a-b90b-487d-bf59-94b8bb8a2666&ds=xnAkkfKkn5QOHZd7",
            },
        ]

        print("Seeding advanced hotel details...")

        try:
            for data in hotel_details:
                hotel = db.session.get(Hotel, data["id"])

                if hotel:
                    hotel.description = data["description"]
                    hotel.rating = data["rating"]
                    hotel.image_link = data["image_link"]
                    # --- NEW COLUMNS ---
                    hotel.maps_link = data["maps_link"]
                    hotel.latitude = data["latitude"]
                    hotel.longitude = data["longitude"]
                    hotel.booking_link = data["booking_link"]

                    print(f"Updated existing hotel: {hotel.name}")
                else:
                    new_hotel = Hotel(
                        id=data["id"],
                        name=data["name"],
                        description=data["description"],
                        rating=data["rating"],
                        image_link=data["image_link"],
                        # --- NEW COLUMNS ---
                        maps_link=data["maps_link"],
                        latitude=data["latitude"],
                        longitude=data["longitude"],
                        booking_link=data["booking_link"],
                    )
                    db.session.add(new_hotel)
                    print(f"Added new hotel: {new_hotel.name}")

            db.session.commit()
            print(
                "✅ Hotel descriptions, ratings, images, coordinates, and links successfully saved!"
            )

        except Exception as e:
            db.session.rollback()
            print(f"❌ An error occurred while saving details: {e}")
