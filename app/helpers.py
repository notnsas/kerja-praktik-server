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
        ratings, and image links.
        """
        hotel_details = [
            {
                "id": 158986,
                "name": "Abams Gili Air",
                "description": "Terletak di Gili Air dekat Pantai Gili Air dan Pelabuhan Bangsal, Abams Gili Air menawarkan B&B berfasilitas lengkap dengan WiFi gratis, AC, teras, kamar mandi bershower, pilihan sarapan harian, serta layanan rental sepeda dan mobil.",
                "rating": 8.1,
                "image_link": "static/348460500.jpg",
            },
            {
                "id": 158990,
                "name": "Pandan Bungalow",
                "description": "Pandan Bungalow yang terletak beberapa langkah dari Pantai Gili Air menawarkan akomodasi nyaman dengan kolam renang outdoor, area pantai pribadi, restoran, layanan kamar, WiFi gratis, serta kamar-kamar ber-AC yang menyuguhkan pemandangan taman.",
                "rating": 7.9,
                "image_link": "static/248990987.jpg",
            },
            {
                "id": 161014,
                "name": "Mantra Gili",
                "description": "Berlokasi di Gili Trawangan dekat lokasi populer, Mantra Gili menyediakan kamar-kamar ber-AC yang dilengkapi TV, brankas, dan kamar mandi pribadi, ditambah fasilitas kolam renang outdoor, WiFi gratis, pilihan sarapan harian, serta rental kendaraan.",
                "rating": 9.0,
                "image_link": "static/402678080.jpg",
            },
            {
                "id": 163277,
                "name": "Kaluku Gili Resort",
                "description": "Menawarkan bungalow tradisional terinspirasi gudang beras dengan pemandangan laut atau gunung, Kaluku Gili Resort terletak hanya 2 menit dari Pantai Gili Air dan dilengkapi dengan fasilitas modern, kolam renang, layanan pijat, serta akses mudah ke berbagai aktivitas air.",
                "rating": 8.9,
                "image_link": "static/250240723.jpg",
            },
            {
                "id": 169082,
                "name": "Bougenville Homestay",
                "description": "Bougenville Homestay menawarkan akomodasi nyaman dengan restoran, taman, teras, WiFi gratis, dan kamar mandi pribadi, berlokasi ideal bagi Anda yang ingin menikmati kegiatan snorkeling atau mengunjungi berbagai atraksi di sekitarnya.",
                "rating": 8.4,
                "image_link": "static/855549673.jpg",
            },
            {
                "id": 174792,
                "name": "Shefa Private Villa",
                "description": "Shefa Private Villa di Gili Trawangan menawarkan pengalaman menginap eksklusif dengan kolam renang pribadi, dapur lengkap, dan area keluarga dalam vila 1 kamar tidur ber-AC yang juga menyediakan sepeda gratis, WiFi gratis, serta sarapan harian.",
                "rating": 9.1,
                "image_link": "static/412129557.jpg",
            },
            {
                "id": 193394,
                "name": "Bintang Darmawan Villa (BDV)",
                "description": "Bintang Darmawan Villa (BDV) di Gili Trawangan menawarkan penginapan nyaman dengan kolam renang outdoor, teras, dan bar. Berjarak dekat dari Pantai Timur Laut dan Pelabuhan Gili Trawangan, hotel ini menyediakan kamar-kamar ber-AC berfasilitas lengkap dengan WiFi gratis, serta akses mudah untuk menjelajahi pulau.",
                "rating": 8.2,
                "image_link": "static/125976922.jpg",
            },
            {
                "id": 201589,
                "name": "Bungalow No 7",
                "description": "Terletak di tepi pantai Nusa Lembongan yang tenang, Bungalow No 7 adalah akomodasi kelolaan keluarga yang dikelilingi taman tropis. Menawarkan kamar ber-AC dengan interior kayu bernuansa alam, resor ini juga dilengkapi dengan restoran, fasilitas kelas menyelam, wisata snorkeling, dan akses dekat ke titik selancar populer.",
                "rating": 7.8,
                "image_link": "static/28671898.jpg",
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
                    print(f"Updated existing hotel: {hotel.name}")
                else:
                    new_hotel = Hotel(
                        id=data["id"],
                        name=data["name"],
                        description=data["description"],
                        rating=data["rating"],
                        image_link=data["image_link"],
                    )
                    db.session.add(new_hotel)
                    print(f"Added new hotel: {new_hotel.name}")

            db.session.commit()
            print("✅ Hotel descriptions, ratings, and images successfully saved!")

        except Exception as e:
            db.session.rollback()
            print(f"❌ An error occurred while saving details: {e}")
